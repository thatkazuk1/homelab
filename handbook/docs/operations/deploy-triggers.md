# Operations: Deploy triggers

How a `git push` to the fleet monorepo turns into a running redeploy.

## The model

A single Forgejo repository-level webhook on `kazuki/homelab`, scoped to push events on
`master`, points at one Komodo Procedure: `deploy-all-changed`. That Procedure has one stage,
`Batch Deploy Stack If Changed`, targeting `*` (every Komodo Stack). Every push triggers the
Procedure; `If Changed` compares each Stack's resolved compose config against what's currently
deployed and only redeploys the Stacks that actually differ — everything else is scanned and
skipped in well under a second.

This replaced a per-Stack webhook model (one Forgejo webhook per Komodo Stack, ~20 by the end)
that didn't scale: every new Stack needed its own webhook registered by hand, and every push
fanned out to every registered webhook regardless of what actually changed.

## Why this is safe

`If Changed` diffs resolved config (the equivalent of `docker compose config`), not raw file
bytes — a comment-only edit to a compose file does **not** trigger a redeploy, only a change
that actually affects the resolved service definitions does. Verified live (Sprint 3s): a
full-fleet run against all 19 Stacks with no real changes pending completed in well under a
second with zero unexpected container recreations, confirmed by comparing `docker ps`
`CreatedAt` timestamps across every host before and after.

## Adding a new Stack

Nothing to configure. The Procedure's `*` target picks up any Stack that exists in Komodo at
the time a push lands — create the Stack (see
[Adopting a stack](adopting-a-stack.md)), and the next push to `master` (from any source —
this change, an unrelated change, a Renovate-merged PR) will scan it along with everything
else.

## Modifying or troubleshooting

- The Procedure lives in Komodo UI under Procedures → `deploy-all-changed`. Its one stage's
  target pattern (`*`, or a comma-separated explicit list) is editable there.
- The Forgejo-side webhook lives at `kazuki/homelab` → Settings → Webhooks. It uses the same
  `KOMODO_WEBHOOK_SECRET` as every other Komodo webhook on this fleet — there's no separate
  per-Procedure secret.
- To confirm a push actually reached Komodo: `docker logs komodo-core-1` on
  `komodo-prod-01` (note the `-1` container-name suffix). A successful delivery logs
  `Successfully authenticated incoming webhook resource_type="Procedure"
  resource_id="deploy-all-changed"`, followed by a `RunProcedure` execution trace.
- Manual trigger is always available: Procedure page → Run button in Komodo UI. Useful for
  testing without needing a real push.

## Known caveats

- **`plane`'s `deploy.replicas: ${VAR:-default}` compose syntax** trips Komodo's internal
  config parser on every deploy attempt (`failed to extract stack services... invalid digit
  found in string`), logged as a WARN. This is cosmetic — the deploy proceeds and completes
  correctly despite the WARN, confirmed both via the old per-Stack webhook and the new
  Procedure path (Sprint 3p, re-confirmed Sprint 3s). Not fixed; would require touching
  `plane`'s replica-count secrets, judgment work rather than a quick change.
- **Upstream issue [#1209](https://github.com/moghtech/komodo/issues/1209)** describes env
  vars configured in Komodo's own UI "Environment" field cross-contaminating between Stacks
  during batch/procedure deploys. This fleet doesn't use that mechanism — secrets are injected
  by the `sops exec-env` wrapper at the shell level before Compose ever runs, bypassing
  Komodo's own env-var handling entirely — and a live batch-redeploy test across three
  SOPS-heavy Stacks (`homepage`, `sure`, `plane`) confirmed clean env isolation (Sprint 3s).
  Worth re-checking if this fleet ever adopts Komodo's own UI-managed environment variables
  for a Stack.
- Every push to `master` triggers a full-fleet scan, including pushes with no compose changes
  at all (documentation, this file, unrelated repo housekeeping). `If Changed` makes this cheap
  (sub-second scans, no redeploys when nothing changed), but it is a real behavior difference
  from the old per-Stack model, where only a push touching a given Stack's own webhook path
  triggered anything for it.
