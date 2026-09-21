# sparkyfitness

SparkyFitness — self-hosted nutrition, exercise, and body-metric tracker (a privacy-first MyFitnessPal alternative). Postgres + Node backend + nginx/React frontend. First stack on docker-prod-02, the fleet's second general Docker host.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-02` |
| Category | applications |
| Status | new |
| Public URL | [sparkyfitness.ts.kazuki.uk](https://sparkyfitness.ts.kazuki.uk) |
| Repo path | [`stacks/sparkyfitness/`](https://github.com/meetKazuki/homelab/tree/master/stacks/sparkyfitness) |

## Services

### `sparkyfitness-db`

- **Image:** `postgres:18.3-alpine`
- **Container:** `sparkyfitness-db`
- **Restart policy:** `unless-stopped`

### `sparkyfitness-server`

- **Image:** `codewithcj/sparkyfitness_server:v1.7.0`
- **Container:** `sparkyfitness-server`
- **Restart policy:** `unless-stopped`

### `sparkyfitness-frontend`

- **Image:** `codewithcj/sparkyfitness:v1.7.0`
- **Container:** `sparkyfitness-frontend`
- **Restart policy:** `unless-stopped`
- **Ports:** `3004:80`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/sparkyfitness/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

## What this is

[SparkyFitness](https://github.com/CodeWithCJ/SparkyFitness) — self-hosted nutrition /
exercise / body-metric tracking. Docs: <https://codewithcj.github.io/SparkyFitness/>.

Three containers: `sparkyfitness-db` (Postgres 18), `sparkyfitness-server` (Node/Better Auth
API on `:3010`, internal only), `sparkyfitness-frontend` (nginx + React SPA, published on
`:3004`). The server runs schema migrations on start and creates the limited `sparky_app`
role from the `sparky` superuser connection.

First stack on `docker-prod-02` — the fleet's second general Docker host, provisioned fresh
through the template-clone + Ansible flow.

## Secrets

`secrets.enc.env` (SOPS, ADR-0008) holds:

| Key | Notes |
|---|---|
| `SPARKY_FITNESS_DB_PASSWORD` | Postgres superuser (`sparky`) |
| `SPARKY_FITNESS_APP_DB_PASSWORD` | limited app role (`sparky_app`) |
| `SPARKY_FITNESS_API_ENCRYPTION_KEY` | 64-hex; **changing it invalidates all stored encrypted data** (external data-source creds) |
| `BETTER_AUTH_SECRET` | session signing + 2FA encryption. **Never rotate after any user enables 2FA — it locks them out.** |
| `SPARKY_FITNESS_ADMIN_EMAIL` | not a secret, but kept out of the public repo (ADR-0010). The account that registers with this email is auto-granted admin. |

## First-run

1. Deploy, then open `http://192.168.50.100:3004` (or `https://sparkyfitness.ts.kazuki.uk`
   once the Traefik route is live) and register. Use the email in
   `SPARKY_FITNESS_ADMIN_EMAIL` for that first account to get admin.
2. After the admin account exists, consider setting `SPARKY_FITNESS_DISABLE_SIGNUP: "true"`
   in `compose.yml` (single-household instance) and redeploying.

## Exposure

`SPARKY_FITNESS_FRONTEND_URL` is set to `https://sparkyfitness.ts.kazuki.uk` (tailnet-scoped,
Traefik on `proxy-prod-01`, same pattern as komodo/forgejo/coolify). The direct LAN address
is in `SPARKY_FITNESS_EXTRA_TRUSTED_ORIGINS` so Better Auth also accepts logins over
`http://192.168.50.100:3004` (used for first-run setup and any time the proxy is bypassed).

## Bind mounts

`/opt/homelab/sparkyfitness/{postgresql,backup,uploads}`. Containers run as root (image
default); Postgres chowns its own data subdir to the in-image `postgres` uid on init.
Files under `backup/` and `uploads/` are written root-owned — acceptable for now; add
`PUID`/`GUID` to the server service if that needs to change.

## AI services

Meal-photo scanning and the chat helper need an AI provider, configured in the app under
Settings, AI Services (stored in the database, encrypted with
`SPARKY_FITNESS_API_ENCRYPTION_KEY`; nothing in `compose.yml`). This instance uses Ollama on
`ollama-prod-01` (`http://192.168.30.111:11434`, model `qwen3-vl:4b`, chat tool set **Core**).
The request comes from the server container, so the URL must be reachable from
`docker-prod-02` (LAN address; that VM is not on the tailnet). The laptop can be off, and the
first request after an Ollama restart takes 30–75 s. See the
[`ollama-prod-01` runbook](../runbooks/ollama-prod-01.md).

## Exercise providers

Wger works. Free Exercise DB is enabled but unreliable here: the server's fetch of the dataset
from `raw.githubusercontent.com` times out (IPv6 unreachable plus IPv4 timeouts from the Node
process, while `curl` from the same container succeeds), and v1.7.0 then blocks retries for
5 minutes. It is not fixed; Wger is the working provider.

## Upgrade note

After a version bump, sign-ins can fail with "Database schema mismatch" until the server
container is restarted (`docker restart sparkyfitness-server`). Better Auth caches its schema
check at boot and can race the migrations.

## Renovate

`postgres:18.3-alpine` and both `codewithcj/*:v1.7.0` tags are pinned and tracked by
Renovate like every other stack.

---

*This page is auto-generated from `stacks/sparkyfitness/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/sparkyfitness/notes.md`.*
