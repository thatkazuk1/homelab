# ADR-0008: The `10.10.37.189` Periphery IP anomaly — investigated, unresolved, non-blocking

## Status

Accepted — 2026-07-08

## Context

Since Sprint 3a, Komodo Core's dashboard has intermittently surfaced the address `10.10.37.189`
in connection with Periphery-managed servers, across three independent hosts
(`docker-prod-01`, `core-01`, `nas-01`). Two hypotheses were tested:

1. It's the Periphery container's own bridge-assigned address, being reported to Core as
   the container's "self" address rather than the host's LAN IP.
2. It's something Komodo Core itself reports as a shared/default source address.

Hypothesis 2 was tested and disproven in Sprint 3a: `komodo-prod-01`'s own interfaces
(`192.168.50.111`, `172.17.0.1`, `172.19.0.1`, `172.18.0.1`) don't include it.

Hypothesis 1 was tested this sprint via `docker inspect komodo-periphery --format
'{{json .NetworkSettings.Networks}}'` on all three affected hosts:

| Host | Network | Gateway | Container IP |
|---|---|---|---|
| `docker-prod-01` | `komodo-periphery_default` | `172.21.0.1` | `172.21.0.2` |
| `core-01` | `komodo-periphery_default` | `172.20.0.1` | `172.20.0.2` |
| `nas-01` | `komodo-periphery_default` | `172.24.0.1` | `172.24.0.2` |

(Note: `ip addr show` from inside the container was attempted first, per the original
diagnostic plan, but failed — the `komodo-periphery-sops` custom image has no `iproute2`
installed. `docker inspect` from the host side proved a reliable substitute.)

None of the three hosts' Periphery containers carry `10.10.37.189` on any interface.

## Decision

Categorize as an unexplained, non-blocking anomaly. Both tested hypotheses are ruled out.
Do not spend further Sprint 3b/3c time chasing this. Confirmed operationally safe: Komodo
Core uses the configured `Address` field (`https://192.168.50.X:8120`) for actual
connections to all three servers, all of which report green in the dashboard.

## Reasoning

The address doesn't originate from Periphery's own Docker networking, and it doesn't
originate from Komodo Core's own host interfaces. With both plausible internal sources
ruled out, further diagnosis would require either instrumenting Komodo Core's source
directly or filing upstream — neither is proportionate to a cosmetic dashboard artifact
with zero observed operational impact across three servers over two sprints.

## Consequences

- No further investigation scheduled for Sprint 3b or 3c.
- Worth filing as a GitHub issue against Komodo upstream at some point, for visibility —
  not scheduled, no owner assigned yet.
- If this address ever appears somewhere with actual operational consequence (e.g.
  Komodo Core attempting real traffic to `10.10.37.189` instead of a configured
  Address), this ADR should be reopened — that would mean hypothesis 2 wasn't fully
  ruled out, only ruled out for the interfaces checked.
