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
   explicit `https://` scheme, obtains its own Let's Encrypt certificate — independent of
   fleet Traefik on `proxy-prod-01` entirely.
4. Deploy. Coolify builds the image, runs it, and wires up the Traefik labels itself.
5. **Add the Cloudflare Tunnel ingress rule** (see below) — this is the step that's easy to
   skip, and it's the one that actually determines whether the tenant is publicly reachable
   at all, not just whether it has a valid certificate.

No fleet-side change is required to add a tenant — that's the property ADR-0014 is built
around. The only thing that ever touches fleet Traefik is the Coolify **admin** URL itself
(`coolify.ts.kazuki.uk`), which routes through `proxy-prod-01` the same way `komodo.ts.kazuki.uk`
and `forgejo.ts.kazuki.uk` do.

## Checklist: giving a new public tenant working SSL

Every `*.kazuki.uk` hostname enters the fleet through one shared Cloudflare Tunnel
(`nexus-pve-main`, running on `docker-prod-01`), configured at
`docker-prod-01:/opt/homelab/cloudflared/config/config.yml` — a host file, not tracked in git
(credentials for the tunnel itself live alongside it, also untracked; see
`stacks/cloudflared/notes.md`). This file is what actually decides whether a hostname reaches
Coolify at all. A new public tenant needs **four** things, not three — a fourth item found the
hard way in August 2026 when `status.kazuki.uk` was unreachable despite Coolify itself being
configured correctly:

1. **A Cloudflare Tunnel ingress rule pointed directly at `coolify-prod-01`**, not
   `proxy-prod-01`:
   ```yaml
   - hostname: <tenant>.kazuki.uk
     service: https://192.168.50.30:443
     originRequest:
       noTLSVerify: true
   ```
   Getting this wrong doesn't look like an SSL problem from the outside — it looks like a
   plain 404, because the request either falls through to the tunnel's `http_status:404`
   catch-all or lands on a Traefik instance (fleet or Coolify's) that has no router for the
   hostname. `status.kazuki.uk` had this exact bug: its ingress rule existed, but pointed at
   `192.168.50.107` (`proxy-prod-01`) — copied from the pattern used by every other
   `*.kazuki.uk` hostname — instead of `192.168.50.30`. Check what `dig <hostname>.kazuki.uk
   @1.1.1.1` resolves to (should be a Cloudflare anycast IP) and then check the ingress file
   directly; DNS resolving "correctly" tells you nothing about which origin the tunnel is
   actually forwarding to.

2. **A path-scoped ingress rule for the ACME HTTP-01 challenge**, placed *before* the tenant's
   main rule:
   ```yaml
   - hostname: <tenant>.kazuki.uk
     path: ^/\.well-known/acme-challenge/.*
     service: http://192.168.50.30:80

   - hostname: <tenant>.kazuki.uk
     service: https://192.168.50.30:443
     originRequest:
       noTLSVerify: true
   ```
   Coolify's Traefik validates its own Let's Encrypt certificates via HTTP-01, which requires
   the challenge request to land on Traefik's plain-HTTP entrypoint (port 80 inside
   `coolify-proxy`). Without this rule, *every* request for the hostname — including the ACME
   challenge — gets forwarded to the origin over HTTPS on port 443 per the main ingress rule,
   which lands on Traefik's HTTPS entrypoint instead and gets routed straight into the tenant's
   own app container. Most apps 404 on an unrecognized path, so the challenge fails with a
   plain 404 and Traefik falls back to serving its `TRAEFIK DEFAULT CERT` self-signed
   certificate at the origin.
   **Do not** "fix" this by pointing the *main* rule at port 80 instead of 443 — Traefik's
   plain-HTTP router redirects to HTTPS unconditionally, and since the tunnel always talks a
   fixed scheme to the origin regardless of what the client actually used, that turns into an
   infinite redirect loop for real traffic (this is the exact failure mode `coolify-discovery-2026-07-11.md` documented as the "double-Traefik-chain problem" during the Sprint 3j
   rebuild). Keep the two rules separate, path rule first.
   This is easy to miss because it's invisible for as long as the tenant already holds a valid
   cert from whenever it was first issued — it only bites at renewal time, and because the
   tunnel's `noTLSVerify: true` means cloudflared never checks the origin cert's validity,
   public traffic through Cloudflare keeps working even after the origin cert has silently
   reverted to self-signed. The only visible symptom is that a **LAN-direct** request to the
   tenant (bypassing the tunnel, e.g. `https://<tenant>.kazuki.uk` from a machine using
   AdGuard's direct-IP rewrite) shows a certificate warning. Check origin cert health directly
   with `openssl s_client -connect 192.168.50.30:443 -servername <tenant>.kazuki.uk | openssl
   x509 -noout -issuer -dates` — issuer should be Let's Encrypt, not `TRAEFIK DEFAULT CERT`.

3. **An AdGuard DNS rewrite** for `<tenant>.kazuki.uk → 192.168.50.30`, more specific than the
   fleet's blanket `*.kazuki.uk → 192.168.50.107` rule, so LAN/tailnet clients resolve to
   Coolify directly instead of to fleet Traefik (which has no route for a Coolify tenant).
   Operator-driven UI action (AdGuard's admin, per ADR-0011) — not tracked anywhere in this
   repo.

4. **The domain entered into Coolify's UI with an explicit scheme** — `https://tenant.kazuki.uk`,
   not a bare hostname. A bare hostname produces a broken Traefik router label in this Coolify
   version (4.1.2): `Host()` ends up empty and the domain gets misparsed into a `PathPrefix`
   match instead.

After changing `config.yml`, reload the tunnel with `docker restart cloudflared-tunnel` on
`docker-prod-01` (bounces every `*.kazuki.uk` hostname for a few seconds, not just the one being
added — take a `config.yml.bak-<date>` copy first) and, if a cert needs to be (re-)issued,
`docker restart coolify-proxy` on `coolify-prod-01` to trigger Traefik's ACME retry immediately
instead of waiting for its own backoff schedule.

## Quirks worth knowing (Coolify 4.1.2)

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
  to port 80 — see the checklist below. Public traffic through Cloudflare keeps working
  regardless (the tunnel doesn't validate origin certs), so the only symptom is a cert warning
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
