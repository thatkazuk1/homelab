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
