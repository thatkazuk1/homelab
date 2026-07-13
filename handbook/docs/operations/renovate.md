# Operations: Renovate

Renovate watches the fleet's Docker Compose image tags and opens pull requests when newer
versions are available. This page covers what it does here, how it's scoped, and how to tune
it.

## What it does

Renovate runs weekly and scans every in-scope `compose.yml` for image references, comparing
each tag against what's actually available upstream. When it finds a newer tag, it opens a
PR against `master` with the version bump and, where the upstream registry provides them, the
relevant changelog or release notes in the PR body. Nothing is applied automatically — a PR is
a proposal, not a change to the running fleet, until someone reviews and merges it.

## How it runs

Renovate isn't a standing container. It runs as an ephemeral job inside a Forgejo Actions
workflow (`.forgejo/workflows/renovate.yml`), a plain `docker run renovate/renovate:latest`
step on the existing Forgejo Actions runner — chosen over the JS-based
`renovatebot/github-action` wrapper because the runner's job image has no Node.js installed.
Configuration lives in `renovate.json` at the repo root, picked up automatically since the
config was committed directly (Renovate's own onboarding-PR flow was skipped).

## Cadence

Weekly, `before 4am on Monday` in `Africa/Lagos` (`0 2 * * 1` UTC in the workflow's cron —
Lagos has no DST, so this doesn't drift across the year). The schedule gates branch/PR
*creation*, not just when the job runs — a manual `workflow_dispatch` trigger outside the
window will run Renovate but won't open new branches until the next scheduled window.

## Scope

Renovate covers `stacks/*/compose.yml` (via `docker-compose.managerFilePatterns`) and
`handbook/Dockerfile` (via `dockerfile.managerFilePatterns`). Four meta-infra directories are
excluded via `ignorePaths` — `stacks/komodo/`, `stacks/komodo-periphery/`, `stacks/forgejo/`,
`stacks/forgejo-runner/` — since these are the fleet's own control-plane services, not
application workloads, and their update cadence gets deliberate human judgment rather than
automated PRs. Coolify tenants are out of scope by design (see **Architecture → Coolify** and
ADR-0016) — Coolify manages its own tenant updates.

## No-auto-merge posture

Every Renovate PR is operator-reviewed and manually merged, same as any other PR against this
repo (ADR-0013: the operator drives UI actions, including merges). There's no automerge rule
configured, deliberately — image bumps can carry breaking changes even at minor/patch
versions, and this fleet doesn't yet have the automated test coverage that would make
unattended merges safe.

## Adding a dependency to scope

A dependency is in scope automatically if it's an image reference inside a `compose.yml`
under `stacks/*/` (and not one of the excluded meta-infra directories) or the `handbook/`
Dockerfile. Adopting a new stack under `stacks/<name>/compose.yml` brings its images into
Renovate's scope with no config change needed. To exclude a stack, add its path to
`ignorePaths` in `renovate.json`.

## Tuning grouping and labels

Two `packageRules` entries currently apply:

- Any `major`-version update gets the `update:major` label, so major bumps are easy to spot
  in the PR list without opening each one.
- Any package matching `postgres` is grouped into a single combined PR (`groupName:
  "postgres"`) rather than one PR per Postgres-based image, since this fleet runs several
  Postgres-backed stacks and bumping them together is usually the more sensible review unit.

Both are ordinary `packageRules` entries — add another block with a `matchPackagePatterns` or
`matchUpdateTypes` filter and a `groupName` or `labels` key to change grouping or labeling
behavior for other packages. Keep tuning changes small and targeted rather than revisiting the
whole config at once; `config:recommended` (the base preset) already covers most sensible
defaults.

## First real run

Renovate's first scheduled run (2026-07-13) opened two PRs, both patch bumps against
`stacks/plane/compose.yml` — `rabbitmq` (`3.13.6` → `3.13.7`) and `valkey/valkey` (`7.2.11` →
`7.2.13`). Scope was correct (in-scope stack only, no meta-infra), and neither carried the
`update:major` label, correctly, since neither is a major bump. The Postgres-grouping rule
hasn't fired yet — no Postgres-image bump has landed in a run so far.
