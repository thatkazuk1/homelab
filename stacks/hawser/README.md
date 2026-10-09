# Hawser agents (Dockhand remote management)

One compose file per host (`compose.<host>.yml`), not a shared template —
same precedent as `stacks/komodo-periphery/` (Sprint 3i): per-host drift
(token, host identity) means a single generic file would misrepresent the
fleet. All hosts except `nas-01` run an identical Standard-mode Hawser agent
aside from the per-host `TOKEN` value, so those files are byte-identical except
for that one line — this is expected, not an oversight. `nas-01` runs in Edge
mode (see below).

## Scope (Sprint 3r, Session 2; `nas-01` closed Sprint 3w)

Deployed and live as real Komodo Stacks on 8 hosts (verified against
Komodo's own `ListStacks` API, Sprint 3y):

- `core-01`
- `coolify-prod-01`
- `plane-prod-01`
- `garage-prod-01`
- `telemetry-prod-01`
- `proxy-prod-01`
- `docker-prod-02` (added after the original rollout)
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

## Network restriction (2026-10-09)

Hawser speaks plain HTTP on port 2376, and the token travels in the `X-Hawser-Token` header.
Every agent publishes `0.0.0.0:2376`. Only Dockhand on `docker-prod-01` (`192.168.50.105`)
needs to connect. All agents are on VLAN 50, and OPNsense does not see intra-VLAN traffic.
So each Hawser host has two `iptables` rules in the `DOCKER-USER` chain:

```bash
sudo iptables -I DOCKER-USER 1 -p tcp --dport 2376 -s 192.168.50.105 -j RETURN
sudo iptables -I DOCKER-USER 2 -p tcp --dport 2376 -j DROP
```

These rules apply to the Standard-mode hosts. `nas-01` does not need them (Edge mode, see
below). If `nas-01` is ever rolled back to Standard mode, run the commands there as
`nexus-tnas` without `sudo`, because `sudo` there does not give real root.

On the `docker_hosts` Hawser hosts, the Ansible role `host_firewall` makes these rules
persistent. The hosts are `telemetry-prod-01`, `plane-prod-01`, `coolify-prod-01`,
`garage-prod-01`, `proxy-prod-01` and `docker-prod-02`. The role puts the same rules in the nft
table `inet homelab_fw` (accept from `192.168.50.105`, drop other IPv4 sources, drop IPv6). The
table loads at boot from `homelab-fw.service`. These rules are enforced even when the role runs
in observe mode. After the table loads, the role removes the manual `iptables` and `ip6tables`
rules. See `ansible/roles/host_firewall/README.md`.

On `core-01`, the role manages the same rules (`host_firewall_hawser: true` in
`ansible/inventory/host_vars/core-01.yml`, applied 2026-10-09). `core-01` is in the inventory
group `firewall_only_hosts`.

## `nas-01`: Edge mode (since 2026-10-09)

`nas-01` runs Hawser in **Edge mode**, so it needs no firewall rule. The agent connects out to
Dockhand at `wss://dockhand.ts.kazuki.uk/api/hawser/connect` (through Traefik, over HTTPS) and
sends its token after the WebSocket opens. The compose file publishes no port. Hawser still
runs a health server on port 2376 **inside** the container only:
`docker exec hawser wget -qO- http://127.0.0.1:2376/_hawser/health` shows `"mode":"edge"` and
`"connected":true`.

- The Dockhand environment `nas-01` has the type "Hawser Edge". It was changed **in place**.
  Never delete and re-create an environment: the delete cascades and removes its history.
- Agent mode is set by environment variables: `DOCKHAND_SERVER_URL` plus `TOKEN` gives Edge
  mode; `TOKEN` alone gives Standard mode.
- Management of `nas-01` now also needs Traefik on `proxy-prod-01` and DNS. The agent reconnects
  by itself (backoff from 1 s to 60 s).
- Rollback: revert the compose change, set the Dockhand environment back to Hawser Standard
  with host `192.168.50.163` and port 2376, and restore the manual rules above.

The other Hawser hosts can move to Edge mode in the same way. Then the Hawser rules in
`host_firewall` (`host_firewall_hawser`) can be removed.

Verification: from `docker-prod-01`, `curl http://<host>:2376/_hawser/info` gets `401`
(reaches Hawser). From any other host, the same request times out.

## Secrets

`secrets.enc.env` holds one `HAWSER_TOKEN_<HOST>` per host, SOPS-encrypted
per ADR-0008. Each per-host compose file references only its own token var.
Komodo Stack's `compose_cmd_wrapper` is `sops exec-env secrets.enc.env`.

## Project name

All per-host Stacks use the same Komodo Project Name (`hawser`) — short and
consistent across hosts, matching the handoff's Phase 4 plan. Server binding
differentiates them, not the project name.
