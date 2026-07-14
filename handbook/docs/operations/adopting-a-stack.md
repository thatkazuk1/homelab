# Operations: Adopting a stack

This is the playbook for bringing a manually-run Docker Compose stack under GitOps
management — proven across a dozen-plus real adoptions. Follow it in order; the sequence
matters, especially around backups and verification.

## 1. When to adopt

A stack is a candidate when it's currently running by hand (`docker compose up` from a host
directory, no Komodo involvement) and you want its lifecycle — deploys, config changes,
rollbacks — driven from the git repo instead. Nothing about adoption requires downtime by
itself; the goal is to bring an existing running stack under reconciliation without disrupting
it.

## 2. Pre-flight verification

Before touching anything, understand exactly what's running. On the host:

```bash
docker compose ls
docker compose ps -a
docker compose config
docker volume ls | grep <project>
cat .env
```

This tells you the real project name (which must match what Komodo will later be told),
every container and its current state, the fully-resolved compose config (including any
env-var interpolation already in effect), the named volumes actually in use, and what's
currently in the `.env` file. Don't assume any of this from the compose file alone — resolved
config and declared config can differ.

## 3. Backup discipline

Mandatory for any stack holding real user data. Not optional, not "if there's time." The
proven pattern:

- **Postgres (or similar DB):** dump over the container's actual network path, not
  `localhost` — some setups have a `trust`-auth rule on `localhost` that will validate any
  password and mask a real credential problem. `pg_dumpall` against the container's network
  alias is the safe default.
- **Named volumes:** tar each one via a throwaway `alpine` container mounting the volume
  read-only, rather than trying to copy files off a running application container directly.
- **Stack directory:** tar the host directory itself (compose file, any bind-mounted config,
  the `.env`).

Offload every artifact off the host before adoption begins — to `nexus-v` or another durable
location. Confirm the artifacts exist and are non-trivial in size before proceeding; a 0-byte
dump is not a backup. This is the same discipline that protected real data during past
adoptions of stateful stacks like Vaultwarden and Sure.

## 4. Repo preparation

Copy the compose file into the repo at `stacks/<name>/compose.yml` (flat layout — no
per-host directory nesting; see [Conventions](../conventions/index.md)). Verify it's byte-for-byte
identical to the host's copy:

```bash
sha256sum compose.yml                    # on the host
sha256sum stacks/<name>/compose.yml      # in the repo, after copying
```

Then adjust bind-mount paths to be absolute. Komodo's Periphery agent clones the repo into
its own container-internal directory — not the host's stack directory — so any relative bind
path in the compose file resolves against the wrong location once Periphery runs it. Absolute
host paths (`/opt/homelab/<name>/data:/data`, or the `nas-01` equivalent) are required.

## 5. Secret assessment

Read the actual `.env` and compose file together before deciding how to handle secrets — don't
default to one pattern before reading. Three shapes show up in practice:

1. **Env-based secrets** — real values in `.env`, referenced via `environment:` or `env_file:`
   in the compose file. These follow the standard pattern: a `stacks/<name>/secrets.enc.env`
   SOPS-encrypted file, plus the universal `compose_cmd_wrapper`. See
   [Getting Started: SOPS and age](../getting-started/sops.md) for the mechanics.
2. **Bind-mounted config files with embedded secrets** — some stacks (Garage, cloudflared)
   keep real credentials inside a bind-mounted config file rather than an env var. These stay
   host-side, unencrypted in the repo sense, because the file itself never enters git — no
   SOPS conversion needed.
3. **Mixed** — apply each pattern to the secrets it actually matches. Don't force a stack with
   both shapes into a single pattern.

Some stacks genuinely have no real secrets at all (a public key, an inert default) — confirm
this by reading, not by assuming from the stack's category.

## 6. Komodo Stack creation

This step is UI-driven, performed by the operator — Komodo authentication isn't available to
the executing agent. The operator needs these exact values ahead of time:

- **Name** — matches the stack's directory name under `stacks/`.
- **Server** — the Komodo Server resource for the target host.
- **Repo / Branch** — the monorepo, `master`.
- **Run Directory** — `stacks/<name>`.
- **File Paths** — the bare filename, `compose.yml` — **not** `stacks/<name>/compose.yml`.
  Komodo joins Run Directory and File Paths together; a path-prefixed value doubles the
  resolved path and fails with a file-not-found error. This exact mistake has happened more
  than once — always supply the bare filename.
- **Project Name** — must match the project name `docker compose ls` showed in step 2, so
  Komodo's compose invocation attaches to the existing containers rather than creating a
  second, parallel project.
- **Wrapper** — only if step 5 found env-based secrets: `sops exec-env secrets.enc.env
  '[[COMPOSE_COMMAND]]'`. Stacks with no secrets, or only file-based ones, get no wrapper.

## 7. Verify adoption without redeploy

Immediately after the operator creates the Stack, check container identity over SSH — same
container IDs and `Created` timestamps as before:

```bash
docker inspect <container> --format '{{.Id}} {{.Created}}'
```

If any ID changed, Stack creation itself triggered a config-driven recreation — meaning
something in the adopted compose file doesn't match the running config. Deleting a Komodo
Stack does **not** stop or remove its containers, so it's safe to delete the Stack, fix the
drift in the repo, and retry.

## 8. Deploy trigger and manual round-trip

No per-Stack webhook setup needed. A single repo-level Forgejo webhook fires the
`deploy-all-changed` Komodo Procedure on every push to `master`; the Procedure runs
`Batch Deploy Stack If Changed` against all Stacks (target `*`), so a newly created Stack is
picked up automatically the next time anything pushes — nothing to register for it
specifically. See [Deploy triggers](deploy-triggers.md) for how the mechanism works.

To verify a new adoption's round trip, force a real redeploy by pushing a small, harmless
change — a marker environment variable is the standard choice, since it's easy to verify
landed without being a real functional change. Expect container recreation within a few
seconds of the push landing. If it doesn't land within a couple of minutes, don't assume this
is normal — check Komodo Core's logs for the webhook delivery and Procedure execution
(`docker logs komodo-core-1`, note the `-1` container-name suffix) before falling back to a
manual Deploy click in the Komodo UI. Auto Update / Poll for Updates is a separate feature
(detects a new image at the same tag, not a git/compose change) and isn't enabled on any
current Stack — don't expect it to fire for a compose-file-driven adoption.

## 9. Functional verification

Targeted, never a blanket dump. Check the specific marker var, a specific health check, or a
specific piece of user-visible functionality — log in and confirm a small number of known
entries or values are present and correct, rather than exhaustively re-verifying everything.

```bash
docker exec <container> printenv MARKER_VAR
```

**Never dump a full secret-bearing structure during verification** — no unfiltered `docker
inspect --format '{{.Config.Env}}'`, no `SELECT *` on a config table, no printing a whole
config file that might contain credentials. Grep for the specific key, check a field's
presence rather than its value. This project has had real credential exposures into
executor-session transcripts from exactly this shortcut — it's a discipline worth holding to
even when it feels like extra typing.

## 10. Retire the host `.env`

Once the stack is verified working end-to-end through the GitOps pipeline, rename (don't
delete) the host-local `.env`:

```bash
mv .env .env.retired-$(date -Idate)
```

Keep it for about a week as a rollback tripwire, then delete it. This closes the loop —
`secrets.enc.env` in the repo becomes the single source of truth, and the host-local
plaintext copy stops being a second place secrets could drift.
