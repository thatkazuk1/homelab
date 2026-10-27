# crowdsec-manager

Web UI for the CrowdSec engine on proxy-prod-01. The fleet Traefik serves it at crowdsec.ts.kazuki.uk behind a strict allowlist and a basic-auth login. A socket proxy limits the Docker API to the crowdsec container.

## Reference

| Field | Value |
|---|---|
| Host | `proxy-prod-01` |
| Category | security |
| Status | new |
| Public URL | [crowdsec.ts.kazuki.uk](https://crowdsec.ts.kazuki.uk) |
| Repo path | [`stacks/crowdsec-manager/`](https://github.com/meetKazuki/homelab/tree/master/stacks/crowdsec-manager) |

## Services

### `crowdsec-manager`

- **Image:** `hhftechnology/crowdsec-manager:2.4.1@sha256:033dd76360e5f5da01b21084921e1f82cef226ebc53e33f77f4128da8d01be2e`
- **Container:** `crowdsec-manager`
- **Restart policy:** `unless-stopped`

### `crowdsec-manager-socket-proxy`

- **Image:** `wollomatic/socket-proxy:1.13.2@sha256:ff95d6ff6c27853005ef85eb8f4ab5923dc3d2f1e055f98fb6aeeaceec3fe848`
- **Container:** `crowdsec-manager-socket-proxy`
- **Restart policy:** `unless-stopped`

## Named volumes

- `crowdsec-manager-config`
- `crowdsec-manager-data`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Related decisions

- [ADR-0009](../decisions/0009-flat-stack-layout.md)

## Operational notes

- Purpose: web UI for the CrowdSec engine on `proxy-prod-01`. Address: `https://crowdsec.ts.kazuki.uk`.
- The tool has no login of its own (upstream issue 132). Without a front proxy, anyone who reaches the port controls CrowdSec and, through the Docker API, the host. The Traefik login is the only user check. Do not publish the container port. Do not add the `crowdsec` middleware or a public route.
- Allowlist: the route uses its own middleware `crowdsec-manager-allowlist`, not `tailscale-whitelist`. It allows the tailnet (`100.64.0.0/10`), the tailscaled gateway address (`172.18.0.1/32`) and the ADMIN VLAN (`192.168.30.0/24`). The LAB VLAN is not allowed, on purpose.
- Operator step before the first deploy: on `proxy-prod-01`, create the login file with `htpasswd -nB <user> > /opt/homelab/gateway/traefik/secrets/crowdsec-manager-users`. `htpasswd` asks for the password, and the line goes to the file only. Then run `setfacl -b` and `chmod 600` on the file. Keep the password in the password manager. The password never goes into chat or git. Without the file, Traefik disables the route.
- The tool runs `cscli` inside the `crowdsec` container through the Docker API. It needs no CrowdSec key. The stack has no `secrets.enc.env`.
- A socket proxy (`wollomatic/socket-proxy`) allows Docker API calls for the `crowdsec` container ID only. **After every recreate of the `crowdsec` container, replace the four copies of the ID in `compose.yml` through a PR.** Get the new ID with `docker inspect crowdsec --format '{{.Id}}'` on `proxy-prod-01`. Until then, the UI shows Docker errors.
- Traefik blocks `/api/terminal`, `/api/update` and `/api/services/shutdown` (router `crowdsec-manager-blocked`).
- The Traefik pages of the tool do not work, because its default paths do not match our Traefik. This is intended.
- Do not use these features: bouncer delete (upstream issue 118 deletes all bouncers, and the Traefik plugin then fails open without a sign), Discord webhook and other keys (stored in plain text in the data volume), console enroll, captcha setup, and Traefik whitelist.
- Edits on the profiles, scenarios and whitelist pages change files in `/opt/homelab/gateway/crowdsec/config` on the host. Make a copy first and delete it after the check.
- Data: volume `crowdsec-manager-data` (`settings.db` and `history.db`, which hold decisions and alerts) and volume `crowdsec-manager-config`.

---

*This page is auto-generated from `stacks/crowdsec-manager/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/crowdsec-manager/notes.md`.*
