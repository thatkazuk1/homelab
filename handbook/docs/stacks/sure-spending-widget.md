# sure-spending-widget

Cron job that calls Sure Finance's MCP endpoint for the current week and month-to-date spend, and writes a flat JSON file that Homepage's "Spent This Week" / "Spent This Month" customapi widgets read as a static file. Exists because neither Sure's REST API nor Homepage's customapi widget can do the aggregation on their own - see notes.md.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | automation |
| Status | new |
| Repo path | [`stacks/sure-spending-widget/`](https://github.com/meetKazuki/homelab/tree/master/stacks/sure-spending-widget) |

## Services

### `aggregator`

- **Image:** `alpine:3.20`
- **Restart policy:** `unless-stopped`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/sure-spending-widget/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

- Exists because Sprint (spending-widget) found no way to get Sure's own
  pre-aggregated spend total onto Homepage without an intermediary:
  `/api/v1/summary` doesn't exist on the running version, `/api/v1/transactions`
  supports `start_date`/`end_date` but has no server-side sum and doesn't apply
  the same transfer/investment-contribution exclusions as Sure's dashboard, and
  MCP's `get_income_statement` (which does match the dashboard exactly - same
  `income_statement.expense_totals` call as `pages_controller.rb`) wraps its
  JSON in a JSON-RPC envelope with the payload double-JSON-encoded as a string,
  which Homepage's `customapi` field mapping can't unwrap on its own.
- "Spent" = Sure's own `expense_totals` definition: excludes `funds_movement`,
  `one_time`, and `cc_payment` transaction kinds, and investment
  Transfer/Sweep/Exchange activity - i.e. matches what Sure's own dashboard
  cash-flow widget shows for the same period, by construction (same query).
- Week = Monday start (Rails' ActiveSupport default, unmodified by this app -
  confirmed by reading `app/models/period.rb`'s `current_week` and this
  family's settings). Month = calendar month-to-date, no custom month start
  configured for any family on this instance (confirmed live).
- Credential: reuses `MCP_API_TOKEN`/`MCP_USER_EMAIL` from `stacks/sure` rather
  than a fresh per-consumer credential - a deliberate, operator-approved
  exception to the one-credential-per-consumer rule. Sure has no lightweight
  read-only MCP credential mechanism: Doorkeeper-authenticated MCP calls
  require `read_write` scope in the app's own code, and minting one requires a
  full interactive OAuth flow (dynamic client registration + browser
  authorization + refresh-token handling) meant for apps like Claude.ai, not a
  cron script. Values duplicated (not referenced) into this stack's own
  `secrets.enc.env`, per this fleet's existing shared-credential convention.
- Output lands at `/opt/homelab/homepage/assets/data/sure-spending.json` on
  `docker-prod-01`, which the `homepage` stack bind-mounts to
  `/app/public/data` - Homepage's own Next.js server serves it as a static
  file, so the widget's `customapi` call never needs a network hop or an
  intermediary service. `stacks/homepage/compose.yml` carries that mount
  (git-tracked); `services.yaml` itself is host-only, never tracked in this
  repo - see `stacks/homepage/notes.md`.
- No REST fallback was picked despite being the "properly scoped credential"
  option, because it would silently drift from Sure's own numbers for anyone
  with transfers, credit-card payments, or investment contributions - accuracy
  against Sure's own dashboard was weighted over credential elegance here.

---

*This page is auto-generated from `stacks/sure-spending-widget/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/sure-spending-widget/notes.md`.*
