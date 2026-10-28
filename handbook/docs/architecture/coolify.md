# Coolify

Coolify is the fleet's second deployment layer — a self-hosted PaaS running on
`coolify-prod-01`, sitting deliberately outside the Komodo/GitOps pipeline described in
**Architecture → Overview**. It's where tenant-shaped workloads live: things that want their
own build pipeline, their own routing, and their own pace of change, rather than a compose file
declared once and reconciled by Periphery.

## Why it's separate from Komodo

Komodo's model assumes a stack's compose file and running state are reconciled from git —
Komodo (or the operator) owns the truth, and drift gets corrected. Coolify doesn't fit that
model: it self-upgrades on its own schedule, rewriting its own `docker-compose.yml` and `.env`
independently of git every time it does. Putting Coolify itself under Komodo would mean either
the two fight over ownership of the same files, or Coolify's auto-upgrade has to be disabled —
a real behavior change, not a free abstraction. So Coolify stays a deliberate operational
island: excluded from Komodo, its own upgrade mechanism authoritative for itself, its tenants'
secrets living in its own UI/database rather than this repo's SOPS pattern. See ADR-0002 (why
Komodo exists) and ADR-0014 (Coolify's own operational standard) for the full reasoning.

The two systems aren't in tension day to day — they answer different questions. Komodo asks
"does the fleet match git?" Coolify asks "is this tenant's app running the version I told it
to build?" A workload only needs Komodo if the answer to the first question matters for it.

## How a new tenant gets deployed

Through Coolify's own UI, not a pull request against this repo:

1. **+ New → Resource**, choose a source — a git repository (public or via a connected
   account) or a plain Docker image.
2. Pick a build method. For git sources with a Dockerfile, set **Base Directory** if the
   Dockerfile isn't at the repo root (this repo's own monorepo shape needs this — see below).
3. Set a domain. Coolify's Traefik handles routing and, for public domains entered with an
   explicit `https://` scheme, obtains its own Let's Encrypt certificate. The fleet Traefik on
   `proxy-prod-01` does not issue or hold this certificate.
4. Deploy. Coolify builds the image, runs it, and wires up the Traefik labels itself.
5. **Add the Cloudflare Tunnel ingress rule and the fleet Traefik router** (see the checklist
   below). This step decides whether the tenant is publicly reachable at all. It also decides
   whether CrowdSec sees the traffic.

A public tenant needs a fleet-side change: one router in `gateway/traefik/dynamic/router.yaml`
on `proxy-prod-01`. This is a change to the earlier ADR-0014 rule "no fleet-side change to add a
tenant". The reason is CrowdSec. Public tenant traffic now passes the fleet Traefik, which runs
the CrowdSec bouncer and AppSec (observe mode), before it reaches Coolify's own Traefik. A
LAN-only tenant (for example `handbook.lan`) needs no fleet-side change. The Coolify **admin** URL
(`coolify.ts.kazuki.uk`) routes through `proxy-prod-01` in the same way as `komodo.ts.kazuki.uk`
and `forgejo.ts.kazuki.uk`.

## The public path: two hops

Every public tenant hostname takes this path:

```
client -> Cloudflare -> cloudflared tunnel -> fleet Traefik (proxy-prod-01, 192.168.50.107:443)
       -> Coolify Traefik (coolify-prod-01, 192.168.50.30:443) -> app container
```

| Hop | What happens |
|---|---|
| Tunnel | Cloudflare sends the request to a tunnel. Two tunnels exist (see below). Both send the main rule of a tenant to `https://192.168.50.107:443` with `noTLSVerify`. |
| Fleet Traefik | A router with the `crowdsec` middleware checks the client IP (CrowdSec ban list) and sends the request to AppSec in observe mode. The router has `tls: {}` and no `certResolver`, so Traefik serves its default certificate and starts no ACME order for the tenant name. |
| Coolify Traefik | The service `coolify-tenants-service` forwards to `https://192.168.50.30:443` with `passHostHeader: true` and `insecureSkipVerify: true`. Coolify's Traefik routes by Host header and serves its own Let's Encrypt certificate. |

The tenant names in `router.yaml` are `tenant-<name>`. Add one router for each name. All routers
use the one service `coolify-tenants-service`.

Two tunnels exist. Each has its own `config.yml` on its host, and neither file is in git. The
credentials stay beside the file (see `stacks/cloudflared/notes.md`).

| Tunnel | Host | Names |
|---|---|---|
| `nexus-pve-main` | `docker-prod-01` | Fleet names (`jellyfin`, `ntfy`, and others) and `status.kazuki.uk`. |
| `coolify-prod-01` | `coolify-prod-01` | `netwright.kazuki.uk`, `school.kazuki.uk`, and the `oriweave.dev` names (`oriweave.dev`, `api`, `docs`, `dev`, `api-dev`, `docs-dev`). |

### How the real client IP reaches CrowdSec

1. Cloudflare adds the connecting client IP to the end of `X-Forwarded-For`.
2. The `websecure` entrypoint trusts `192.168.50.30` and `192.168.50.105` (the two tunnel
   hosts) in `forwardedHeaders.trustedIPs`. Traefik keeps `X-Forwarded-For` from these sources.
   It deletes `X-Forwarded-*` from every other source.
3. The CrowdSec bouncer plugin reads the last entry of `X-Forwarded-For` as the client IP. The
   plugin falls back to the connection address when the header is empty. The plugin does not
   read `CF-Connecting-IP`.
4. The access log field `ClientHost` shows this IP. `ClientAddr` shows the tunnel host.

Coolify's Traefik has no `forwardedHeaders.trustedIPs` flag. It deletes `X-Forwarded-*` and sets
`X-Forwarded-For` to `192.168.50.107`. An app that needs the real IP must read `CF-Connecting-IP`.
Before the gateway path the app saw a Docker address in `X-Forwarded-For`, so this is not a
new limit. To let the apps see the real IP in `X-Forwarded-For`, an operator can add the flag
`--entrypoints.https.forwardedHeaders.trustedIPs=192.168.50.107/32` in the Coolify UI
(Servers, Proxy, Configuration). Coolify keeps custom proxy flags. This flag is not set today.

## Checklist: giving a new public tenant working SSL

A new public tenant needs **five** things. Item 4 was found in August 2026, when
`status.kazuki.uk` was unreachable although Coolify itself was correct.

1. **A Cloudflare Tunnel ingress rule that points at the fleet Traefik**, in the `config.yml`
   of the tunnel that carries the name:
   ```yaml
   - hostname: <tenant>.kazuki.uk
     service: https://192.168.50.107:443
     originRequest:
       noTLSVerify: true
   ```
   A wrong target does not look like an SSL fault. It looks like a plain 404. The request falls
   through to the `http_status:404` catch-all, or reaches a Traefik that has no router for the
   name. Check the ingress file directly. A DNS name that resolves to a Cloudflare IP tells you
   nothing about the target of the tunnel.

2. **A path-scoped rule for the ACME HTTP-01 challenge, before the main rule.** This rule goes
   straight to Coolify's port 80. It does not pass the fleet Traefik, so CrowdSec does not see
   these requests. This is accepted: the path returns 404 unless a challenge is pending.
   ```yaml
   - hostname: <tenant>.kazuki.uk
     path: ^/\.well-known/acme-challenge/.*
     service: http://localhost:80        # tunnel on coolify-prod-01
                                         # use http://192.168.50.30:80 in the docker-prod-01 tunnel

   - hostname: <tenant>.kazuki.uk
     service: https://192.168.50.107:443
     originRequest:
       noTLSVerify: true
   ```
   Coolify's Traefik gets its Let's Encrypt certificates with HTTP-01. The challenge must reach
   the plain-HTTP entrypoint (port 80 of `coolify-proxy`). Without this rule the challenge goes
   to the app, the app returns 404, and the Coolify Traefik falls back to its
   `TRAEFIK DEFAULT CERT` self-signed certificate.
   **Do not** point the main rule at port 80. The plain-HTTP router of Coolify redirects to
   HTTPS, and the tunnel always uses a fixed scheme to the origin. That causes an infinite
   redirect loop (the "double-Traefik-chain problem" from the Sprint 3j rebuild). Keep the two
   rules separate. Put the path rule first, because the first matching rule wins.
   Test the order with `cloudflared tunnel --config <file> ingress rule <url>`.

3. **A router in fleet Traefik** (`gateway/traefik/dynamic/router.yaml`, applied by hand to
   `proxy-prod-01`; see the Traefik notes in the `pve-cluster` runbook):
   ```yaml
   tenant-<name>:
     entrypoints:
       - websecure
     rule: "Host(`<tenant>.kazuki.uk`)"
     service: coolify-tenants-service
     middlewares:
       - crowdsec
     tls: {}
   ```
   Use `tls: {}` and no `certResolver`. An empty `tls` block does not inherit the `certResolver`
   of the entrypoint. A `certResolver` here makes Traefik start an ACME order for the name, and
   the Cloudflare DNS token may not cover the zone.

4. **The domain entered in the Coolify UI with an explicit scheme**: `https://tenant.kazuki.uk`,
   not a bare host name. A bare host name gives a broken Traefik router label in the Coolify
   versions that were tested (`Host()` is empty and the name becomes a `PathPrefix`).

5. **DNS**. The public name is a proxied CNAME to the tunnel. A LAN or tailnet client resolves
   the public name through Cloudflare. If an AdGuard rewrite exists for the name, it must point at
   `192.168.50.107` (fleet Traefik). It must not point at `192.168.50.30`, because that path
   skips CrowdSec. The wildcard `*.kazuki.uk` rewrite was removed on 2026-09-12, so each name
   needs its own rewrite or none. The AdGuard change is an operator UI action and is not tracked
   in this repo.

After a change to a tunnel `config.yml`:

1. Copy the file to `config.yml.pre-<change>` and write the new file as `config.yml.new` in the
   same folder.
2. Run `docker exec cloudflared-tunnel cloudflared tunnel --config /etc/cloudflared/config.yml.new ingress validate`. Expect `OK`.
3. Run `mv config.yml.new config.yml` and `docker restart cloudflared-tunnel`. All names of that
   tunnel are down for a few seconds. The Coolify tunnel carries only the Coolify tenants. The
   `docker-prod-01` tunnel carries the fleet names.
4. If a certificate needs to be issued again, run `docker restart coolify-proxy` on
   `coolify-prod-01`. Traefik then retries ACME at once.
5. Delete the `config.yml.pre-<change>` copy after the check.

### Checking the origin certificate

The tunnel and the fleet Traefik do not verify the certificate of the next hop (`noTLSVerify`
and `insecureSkipVerify`). A Coolify certificate that reverts to the self-signed default
therefore stays hidden: the public site still works. Check the certificate of each tenant
directly from time to time, and after every certificate renewal date:

```bash
openssl s_client -connect 192.168.50.30:443 -servername <tenant> </dev/null 2>/dev/null \
  | openssl x509 -noout -issuer -dates
```

The issuer must be Let's Encrypt, not `TRAEFIK DEFAULT CERT`.

### Failure behavior

- If `proxy-prod-01` is down, all tenant names return a Cloudflare 502. The fleet names depend
  on it in the same way. The rollback for a tenant is to point its main rule back at
  `https://localhost:443` (Coolify tunnel) or `https://192.168.50.30:443` (`docker-prod-01`
  tunnel) and restart the tunnel.
- The bouncer fails open (`updateMaxFailure: -1`). If CrowdSec is down, traffic passes without a
  check.
- Fleet Traefik trusts `192.168.50.30` for `X-Forwarded-For`. A container on `coolify-prod-01`
  can therefore send a forged `X-Forwarded-For` to fleet Traefik. An address in `clientTrustedIPs`
  (`100.64.0.0/10`, `172.16.0.0/12`) makes the bouncer skip the check. The operator accepted
  this risk on 2026-10-27.

## Quirks worth knowing

Coolify 4.5.0 runs on `coolify-prod-01` (checked 2026-10-27). The quirks below were found on
4.1.2. They were not checked again on 4.5.0. Check each one before you rely on it.

A few surface-level bugs and defaults, discovered across two sprints of actually using this
version, worth checking for explicitly rather than assuming they're fixed:

- **The domain field needs an explicit scheme.** A bare hostname produces a broken Traefik
  router label; enter `https://tenant.kazuki.uk` or `http://tenant.lan`, not just the
  hostname.
- **DNS must resolve *before* Coolify will create any route at all** — not just before TLS
  will validate. For a LAN-only domain, the AdGuard rewrite needs to exist first, pointed at
  `coolify-prod-01`, before the application is deployed.
- **"Ports Exposes" doesn't reliably read a Dockerfile's `EXPOSE` line.** It's defaulted to a
  generic guess (`3000`) rather than the actual exposed port on more than one deploy, causing a
  502 until corrected by hand in the app's General settings.
- **The build-time DNS validation runs from inside a container**, using the Docker daemon's
  own resolver (`/etc/docker/daemon.json`, not the host's `/etc/resolv.conf`). If that
  resolver doesn't know about `.lan` names, LAN-only domains fail validation even when the
  host itself resolves them fine.
- **A public tenant's Let's Encrypt cert can silently revert to self-signed at renewal time**
  if the Cloudflare Tunnel doesn't have a path-scoped rule routing the ACME HTTP-01 challenge
  to port 80 — see the checklist above. Public traffic through Cloudflare keeps working
  regardless (neither the tunnel nor the fleet Traefik validates origin certs), so the only symptom is a cert warning
  on LAN-direct access.

## Handbook as a tenant

This handbook is a live example of the pattern above: deployed from the fleet monorepo's
GitHub mirror, `Base Directory` set to `/handbook` so Coolify builds only that subdirectory
against the existing `handbook/Dockerfile`, served at `http://handbook.lan/` — plain HTTP, no
port, no TLS. It replaced an earlier Komodo-Stack-plus-port-exposure setup (see ADR-0013) once
Coolify's LAN-only serving was confirmed to work cleanly.

One caveat carried over from the old pipeline: Coolify has no auto-deploy webhook configured
for this application, so a push to `handbook/` doesn't trigger a rebuild by itself — publishing
a handbook change still needs a manual **Deploy** click in Coolify's UI (see
**Operations → Maintaining the handbook**).
