- Was the first stack adopted into Komodo (Sprint 3b.1), and the reference case for the whole
  adoption pattern — its ~40-variable secret surface turned out to be the largest blast radius
  of any stack adopted to date, larger than Vaultwarden's.
- Widget failures are silent — a service's widget going blank usually means that service is
  unreachable, not that Homepage is broken.
- One known casing oddity in the secrets file, `HOMEPAGE_VAR_K8s_API_KEY`, breaks the fleet's
  all-caps naming convention. Left as-is; not confirmed whether it causes a resolution
  mismatch against the widget config.
