# homepage

A single-page dashboard showing the state of every service in the homelab, aggregating live widget data from each service's own API.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | dashboard |
| Status | adopted |
| Public URL | [home.ts.kazuki.uk](https://home.ts.kazuki.uk) |
| Repo path | [`stacks/homepage/`](https://github.com/meetKazuki/homelab/tree/master/stacks/homepage) |

## Services

### `homepage`

- **Image:** `ghcr.io/gethomepage/homepage:latest`
- **Container:** `homepage`
- **Restart policy:** `unless-stopped`
- **Ports:** `3000:3000`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/homepage/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

- Was the first stack adopted into Komodo (Sprint 3b.1), and the reference case for the whole
  adoption pattern — its ~40-variable secret surface turned out to be the largest blast radius
  of any stack adopted to date, larger than Vaultwarden's.
- Widget failures are silent — a service's widget going blank usually means that service is
  unreachable, not that Homepage is broken.
- The `HOMEPAGE_VAR_K8s_API_KEY` casing oddity (breaking the fleet's all-caps convention) was
  fixed to `HOMEPAGE_VAR_K8S_API_KEY` (Sprint 3q). While tracing it, found the variable isn't
  referenced anywhere in `services.yaml` or `kubernetes.yaml` (the latter is an empty sample
  stub) — there is no live Kubernetes widget configured on this instance. The retired host
  `.env` shows the value was a Kubernetes ServiceAccount token for a `nexus-pve` service
  account, suggesting it's a leftover from the pre-standardization Proxmox/K8s era rather than
  an active integration. Left in place (rename only, per sprint scope) — removal is a judgment
  call for a future pass, not done here.

---

*This page is auto-generated from `stacks/homepage/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/homepage/notes.md`.*
