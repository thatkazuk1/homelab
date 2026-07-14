# Hawser agents (Dockhand remote management)

One compose file per host (`compose.<host>.yml`), not a shared template —
same precedent as `stacks/komodo-periphery/` (Sprint 3i): per-host drift
(token, host identity) means a single generic file would misrepresent the
fleet. All current hosts run an identical Standard-mode Hawser agent aside
from the per-host `TOKEN` value, so the files are byte-identical except for
that one line — this is expected, not an oversight.

## Scope (Sprint 3r, Session 2)

Deployed to the 7 hosts live-confirmed running `portainer-agent` during
Phase 1 discovery (`docs/dockhand-discovery-2026-07-14.md`):

- `core-01`
- `coolify-prod-01`
- `plane-prod-01`
- `garage-prod-01`
- `telemetry-prod-01`
- `proxy-prod-01`
- `komodo-prod-01`

`nas-01` was Portainer-agent-scoped per `docs/project-state.md` but could
not be live-verified this session (SSH times out, matching the documented
TOS quirk — no persistent SSH, browser Terminal only). Deferred to a future
session pending TOS-terminal confirmation, rather than deployed blind.
`docker-prod-01` does not get a Hawser agent — it's where Dockhand itself
runs, visible via its local Docker socket.

## Secrets

`secrets.enc.env` holds one `HAWSER_TOKEN_<HOST>` per host, SOPS-encrypted
per ADR-0010. Each per-host compose file references only its own token var.
Komodo Stack's `compose_cmd_wrapper` is `sops exec-env secrets.enc.env`.

## Project name

All per-host Stacks use the same Komodo Project Name (`hawser`) — short and
consistent across hosts, matching the handoff's Phase 4 plan. Server binding
differentiates them, not the project name.
