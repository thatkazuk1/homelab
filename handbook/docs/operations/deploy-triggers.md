# Operations: Deploy triggers

How a `git push` to the fleet monorepo turns into a running redeploy.

## The model

A single Forgejo repository-level webhook on `kazuki/homelab`, scoped to push events on
`master`, points at one Komodo Procedure: `deploy-all-changed`. That Procedure has **two**
stages, run sequentially:

1. **Sync Resources** — `RunSync` against the `homelab-resources` ResourceSync, reconciling
   Komodo's own resource definitions (servers, stacks, procedures) from
   `komodo/resources/default.toml` (ADR-0017). This runs first so config changes land before
   any deploy is attempted.
2. **Stage 1** — `Batch Deploy Stack If Changed`, targeting `*` (every Komodo Stack). `If
   Changed` compares each Stack's resolved compose config against what's currently deployed
   and only redeploys the Stacks that actually differ — everything else is scanned and skipped
   in well under a second.

This replaced a per-Stack webhook model (one Forgejo webhook per Komodo Stack, ~20 by the end)
that didn't scale: every new Stack needed its own webhook registered by hand, and every push
fanned out to every registered webhook regardless of what actually changed.

**Stack content (compose, `secrets.enc.env`) and Komodo's own resource definitions are both
git-driven, not UI-driven, once a stack is adopted** (ADR-0011's 2026-08-04 amendment). Editing
either live in the Komodo UI without a following export/commit/push creates drift these ADRs
exist to prevent — see `komodo/README.md` for the resource-sync side of that discipline.

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

- **Secrets-only pushes are silently skipped — confirmed, not yet fixed (2026-08-04).**
  `If Changed` diffs *resolved* compose config, and secret vars resolve to `""` in that diff
  (ADR-0008's bare pass-through design) — a push that changes only a stack's
  `secrets.enc.env` shows no diff and the redeploy is skipped, so the new secret never reaches
  the host even though the encrypted file itself syncs correctly. Confirmed via a controlled
  experiment on `speedtest-tracker` (Sprint 4x arc) and reconfirmed this sprint. A same-sprint
  attempt to fix this by making Stage 1 unconditional (`BatchDeployStack` instead of `...
  IfChanged`) was reverted: it works for materialization, but running the full deploy pipeline
  against all ~27 stacks on every push — instead of only the stacks `If Changed` would have
  redeployed anyway — surfaced a DNS resolution contention issue (roughly a third of stacks'
  `git fetch` failing intermittently each run, apparently overwhelming AdGuard on `core-01`
  under the burst). The failures are safe (they abort before touching the running container,
  confirmed) but unacceptable as a standing cost. **Current state: reverted to `If Changed`,
  original gap still open.** Until a targeted fix lands (deploy only the stacks whose files
  actually changed, computed from git diff, still unconditional), verify materialization by
  hand after any secrets-only push — see `updating-a-stacks-secrets.md`.
- **`plane`'s `deploy.replicas: ${VAR:-default}` compose syntax** trips Komodo's internal
  config parser on every deploy attempt (`failed to extract stack services... invalid digit
  found in string`), logged as a WARN. **This is not confirmed cosmetic.** It was believed
  cosmetic (Sprint 3p, re-confirmed Sprint 3s) because the deploy always proceeded and
  completed. The Plane diagnostic (2026-08-03) observed the WARN coincide with a secret
  change **failing to materialize on the host** on one deploy, and materializing fine on
  another — inconsistent, and not yet root-caused. Until that materialization behavior is
  understood, **verify materialization** (sha256/mtime of the deployed file vs. the
  committed one, on the host) after any deploy that changes a secret — do not assume a push
  succeeded just because it completed without error. The root cause is a separate,
  not-yet-scheduled investigation into Komodo's sync/parser internals; this WARN is flagged
  here as a candidate contributor, not a solved question. Not fixed; would also require
  touching `plane`'s replica-count secrets, judgment work rather than a quick change.
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
