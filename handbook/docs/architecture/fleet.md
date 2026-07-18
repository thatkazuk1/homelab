# Fleet Inventory

The hosts currently registered as Komodo Servers, sourced live from Komodo Core's API.

| Host | Address |
|---|---|
| `coolify-prod-01` | `https://192.168.50.30:8120` |
| `core-01` | `https://192.168.50.3:8120` |
| `docker-prod-01` | `https://192.168.50.105:8120` |
| `garage-prod-01` | `https://192.168.50.80:8120` |
| `nas-01` | `https://192.168.50.163:8120` |
| `plane-prod-01` | `https://192.168.50.50:8120` |
| `proxy-prod-01` | `https://192.168.50.107:8120` |
| `telemetry-prod-01` | `https://192.168.50.106:8120` |

Not every fleet host appears here — only hosts Komodo Core has a registered Server entry
for. See [Architecture Overview](overview.md) for the Proxmox cluster nodes and other hosts
outside Komodo's management surface.

---

*This page is auto-generated from Komodo Core's Server API. To regenerate, run:*

```bash
make fleet-inventory
```

*Last regenerated: 2026-07-18T22:24+00:00 UTC*