# sure

Self-hosted personal finance / budgeting app (Rails, formerly known as "Maybe Finance") — accounts, transactions, budgets.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | personal-finance |
| Status | adopted |
| Repo path | [`stacks/sure/`](https://github.com/meetKazuki/homelab/tree/master/stacks/sure) |

## Services

### `web`

- **Image:** `ghcr.io/we-promise/sure:latest`
- **Restart policy:** `unless-stopped`
- **Ports:** `3001:3000`

### `worker`

- **Image:** `ghcr.io/we-promise/sure:latest`
- **Restart policy:** `unless-stopped`

### `db`

- **Image:** `postgres:16`
- **Restart policy:** `unless-stopped`

### `redis`

- **Image:** `redis:8.0.2`
- **Restart policy:** `unless-stopped`

## Named volumes

- `app-storage`
- `postgres-data`
- `redis-data`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/sure/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)
- ADR-0014 (not yet published in the handbook — see `docs/adrs/` on disk)

## Operational notes

- Uses YAML anchors (`x-db-env`, `x-rails-env`) for shared environment blocks — kept as-is
  during adoption rather than rewritten to the bare-pass-through style most other stacks use;
  both work identically with the `sops exec-env` wrapper, and rewriting a working production
  compose structure for stylistic uniformity wasn't worth the risk.
- Two vars present in the original host `.env` (`SECRET_KEY_BASE_II`, `OPENAI_ACCESS_TOKEN`)
  were confirmed unreferenced anywhere in the compose file and dropped, per operator
  confirmation — still an open question whether that silently disables a Sure feature, or
  whether they were just template leftovers.
- A mandatory backup was taken and verified off-host *before* any adoption work touched this
  stack, given the data sensitivity — the strictest pre-flight discipline applied to any
  adoption to date.
- Functional verification exceeded the usual bar: real, live operator browser traffic against
  the redeployed stack (actual 200s on `/transactions`), not just a health-check response.
- Redis runs with no password configured at all in this deployment — a real characteristic of
  the current setup, not a gap introduced by adoption.
- This stack is the origin case for the "never dump a full secret-bearing structure during
  verification" discipline now in `CLAUDE.md` — an early verification step here used an
  unfiltered container-environment dump instead of a targeted grep, which is exactly the
  mistake that rule exists to prevent.

---

*This page is auto-generated from `stacks/sure/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/sure/notes.md`.*
