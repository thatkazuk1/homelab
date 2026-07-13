- The `secrets.enc.env` vars (`PUID`, `PGID`, `TZ`) are trivial — none are actually sensitive,
  included for uniformity with every other adopted stack. The real credentials — an Argo
  Tunnel origin certificate (`cert.pem`) and a `<uuid>.json` credentials file
  (`TunnelID`/`TunnelSecret`/`AccountTag`) — stay host-side under
  `/opt/homelab/cloudflared/config/`, bind-mounted, never committed to git. This is the
  classic named-tunnel model, not the newer token-based one.
- Each redeploy causes the tunnel to briefly drop and reconnect (a few seconds of
  interruption across every `*.kazuki.uk` route it carries) — expected, not a fault.
