# sure

A self-hosted personal finance / budgeting app (Rails, formerly known as "Maybe Finance").

**Host:** `docker-prod-01`
**Access:** port `3001` on the host, domain configured via the secret `APP_DOMAIN` var
**Repo:** [`stacks/sure/`](https://github.com/meetKazuki/homelab/tree/master/stacks/sure)

## What it does

Sure tracks accounts, transactions, and budgets. It's one of the fleet's few genuinely
multi-service, stateful stacks — a Rails web app, a Sidekiq background worker, its own
Postgres database, and its own Redis instance, all under one compose project. It's also, with
`vaultwarden`, one of the highest-stakes stacks in the repo: real financial data, not
easily reconstructed from anywhere else.

## Topology

| Service | Role |
|---|---|
| `web` | Rails app, port 3000 internally (published as `3001`) |
| `worker` | Sidekiq background jobs |
| `db` | Postgres 16 |
| `redis` | Redis 8 |

## Configuration

- **Compose:** uses YAML anchors (`x-db-env`, `x-rails-env`) for shared environment blocks —
  kept as-is during adoption rather than rewritten to the bare-pass-through style most other
  stacks use; both work identically with the `sops exec-env` wrapper, and rewriting a working
  production compose structure for stylistic uniformity wasn't worth the risk.
- **Secrets:** full ADR-0010 pattern — `secrets.enc.env` carries 15 vars actually consumed by
  the compose file: `APP_DOMAIN`, `SECRET_KEY_BASE`, `POSTGRES_PASSWORD`, `SMTP_ADDRESS`,
  `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_TLS_ENABLED`,
  `ACTIVE_STORAGE_SERVICE`, and the five `GENERIC_S3_*` vars for object storage. Two vars
  present in the original host `.env` (`SECRET_KEY_BASE_II`, `OPENAI_ACCESS_TOKEN`) were
  confirmed unreferenced anywhere in the compose file and dropped, per operator confirmation
  — still an open question whether that silently disables a Sure feature, or whether they
  were just template leftovers.
- **Data:** three named volumes (`app-storage`, `postgres-data`, `redis-data`), no explicit
  `name:` fields — Docker's auto-generated names from the original deployment, preserved.

## Notable

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

## See also

- [Adopting a stack](../operations/adopting-a-stack.md)
- [ADR-0010 Per-stack SOPS secrets](../decisions/0010-per-stack-sops-secrets.md)
