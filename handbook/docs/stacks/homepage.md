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
- One known casing oddity in the secrets file, `HOMEPAGE_VAR_K8s_API_KEY`, breaks the fleet's
  all-caps naming convention. Left as-is; not confirmed whether it causes a resolution
  mismatch against the widget config.

---

*This page is auto-generated from `stacks/homepage/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/homepage/notes.md`.*
