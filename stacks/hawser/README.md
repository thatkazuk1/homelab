# Hawser agents (Dockhand remote management)

One compose file per host (`compose.<host>.yml`), not a shared template —
same precedent as `stacks/komodo-periphery/` (Sprint 3i): per-host drift
(token, host identity) means a single generic file would misrepresent the
fleet. All current hosts run an identical Standard-mode Hawser agent aside
from the per-host `TOKEN` value, so the files are byte-identical except for
that one line — this is expected, not an oversight.

## Scope (Sprint 3r, Session 2; `nas-01` closed Sprint 3w)

Deployed and live as real Komodo Stacks on 7 hosts (verified against
Komodo's own `ListStacks` API, Sprint 3y):

- `core-01`
- `coolify-prod-01`
- `plane-prod-01`
- `garage-prod-01`
- `telemetry-prod-01`
- `proxy-prod-01`
- `nas-01` (closed Sprint 3w via TOS browser-Terminal relay; this
  README previously listed it as deferred pending TOS-terminal
  confirmation — stale as of Sprint 3y)

`docker-prod-01` does not get a Hawser agent — it's where Dockhand itself
runs, visible via its local Docker socket.

### `komodo-prod-01` — permanent exception, not deployed

`compose.komodo-prod-01.yml` and a `HAWSER_TOKEN_KOMODO_PROD_01` secret are
committed for documentation purposes, but there is no registered Komodo
Stack for this host (confirmed against `ListStacks`, Sprint 3y) and none is
planned. `komodo-prod-01`'s Periphery runs the vanilla upstream image, not
the `-sops` variant, so the `sops exec-env` wrapper this stack's secret
depends on can't run there — same bootstrap-circularity class as
`stacks/komodo/compose.yml` (Komodo can't cleanly manage its own host).
Formally accepted as a permanent exception Sprint 3y (`x-meta.adr_exceptions`
on the compose file, added Sprint 3x); see CLAUDE.md's Docker-management
coverage-gap note. Not going to be revisited unless `komodo-prod-01`'s
Periphery is upgraded to the `-sops` variant for unrelated reasons.

## Secrets

`secrets.enc.env` holds one `HAWSER_TOKEN_<HOST>` per host, SOPS-encrypted
per ADR-0010. Each per-host compose file references only its own token var.
Komodo Stack's `compose_cmd_wrapper` is `sops exec-env secrets.enc.env`.

## Project name

All per-host Stacks use the same Komodo Project Name (`hawser`) — short and
consistent across hosts, matching the handoff's Phase 4 plan. Server binding
differentiates them, not the project name.
