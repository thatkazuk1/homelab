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

## Renovate

`postgres:18.3-alpine` and both `codewithcj/*:v1.6.4` tags are pinned and tracked by
Renovate like every other stack.
