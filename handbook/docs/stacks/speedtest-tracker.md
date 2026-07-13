# speedtest-tracker

Scheduled internet speed tests with historical tracking and an optional public dashboard view.

## Reference

| Field | Value |
|---|---|
| Host | `telemetry-prod-01` |
| Category | monitoring |
| Status | adopted |
| Repo path | [`stacks/speedtest-tracker/`](https://github.com/meetKazuki/homelab/tree/master/stacks/speedtest-tracker) |

## Services

### `speedtest-tracker`

- **Image:** `lscr.io/linuxserver/speedtest-tracker:latest`
- **Container:** `speedtest-tracker`
- **Restart policy:** `unless-stopped`
- **Ports:** `8080:80`, `8443:443`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/speedtest-tracker/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

- Kept the pre-adoption `${VAR}` interpolation style in the `environment:` block rather than
  rewriting to bare pass-through, matching the precedent set by [sure](sure.md).
- The SQLite database in its config bind mount also holds this app's InfluxDB write-token
  integration as app-managed state, the same pattern [beszel](beszel.md) uses for
  its own S3 config (not an env var).
- A real behavioral regression was caught during adoption's resolved-config diff: the
  original `env_file:` implicitly passed a bare `TZ` value into the container (the LSIO base
  image reads system `TZ` separately from the app's own `DISPLAY_TIMEZONE` setting) — the
  first conversion draft dropped it, restored as an explicit `TZ=${TZ}` pass-through
  alongside `DISPLAY_TIMEZONE`.
- This is the reference case in `docs/project-state.md`'s "Known odd behaviors" for a pair of
  unresolved, Komodo-side transient faults: one deploy where every `${VAR}` substitution came
  through blank despite a correctly-configured wrapper, and a separate silent
  webhook-dispatch stall. Both were resolved by operator-side UI changes, neither
  conclusively root-caused. Worth checking this note if a similar symptom shows up on another
  stack.

---

*This page is auto-generated from `stacks/speedtest-tracker/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/speedtest-tracker/notes.md`.*
