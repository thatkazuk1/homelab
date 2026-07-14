# vaultwarden

A self-hosted, Bitwarden-compatible password vault — holds the fleet's actual password data.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | password-management |
| Status | adopted |
| Repo path | [`stacks/vaultwarden/`](https://github.com/meetKazuki/homelab/tree/master/stacks/vaultwarden) |

## Services

### `vaultwarden`

- **Image:** `vaultwarden/server:latest`
- **Container:** `vaultwarden`
- **Restart policy:** `unless-stopped`
- **Ports:** `8000:80`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/vaultwarden/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

## Admin panel access

Vaultwarden's `ADMIN_TOKEN` environment variable is deliberately unset.
The `/admin` backend UI is not exposed on this instance. Rationale:
the admin panel is a real attack surface, and this fleet does not
require it for normal operation. If admin access is ever needed
(user management, DB inspection, etc.), the token can be set
temporarily and removed after use rather than left configured
permanently.
- Adopted in Sprint 3b.1 with the strictest verification of that sprint's three stacks: a
  pre-adoption backup (both a tarball and an operator-captured native Vaultwarden export),
  and a forced redeploy confirmed via an authenticated vault-entry check rather than just a
  health-check response.
- A shell-quoting bug in the Komodo Wrapper field was hit and fixed by the operator directly
  during setup — fixed, but never documented with a root cause, so if it recurs the diagnosis
  starts from scratch.
- The pre-stop backup tarball was deleted before its checksum comparison completed; the
  off-host copy was confirmed present by size only, not by hash. Low risk given the
  independent native export existed as a second artifact, but a real gap in that sprint's
  verification rigor worth naming honestly.

---

*This page is auto-generated from `stacks/vaultwarden/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/vaultwarden/notes.md`.*
