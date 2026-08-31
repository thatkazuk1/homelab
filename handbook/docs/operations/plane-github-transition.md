# Operations: Plane PR-merge automation

A PR referencing a Plane work item moves that work item's state automatically when the PR
opens or merges — no manual dragging cards across the board. This page covers what it does,
the one-way direction and why, where the token lives, and how to extend it.

## What it does

Two trigger points, both driven by a keyword + work-item identifier in a PR's title or body:

- **PR opened or reopened**, matching `starts`/`start`/`started` before an identifier — moves
  the work item to **In Progress**.
- **PR closed as merged**, matching `close(s|d)`/`fix(es|ed)`/`resolve(s|d)`/`complete(s|d)`
  before an identifier — moves the work item to **Done**.

Example: a PR titled `Fix qbittorrent memory cap` with `Closes HOMELAB-42` in the body moves
`HOMELAB-42` to Done the moment the PR merges. Multiple identifiers in one PR (`Closes FOO-1,
FOO-2 and FOO-3`) all get picked up.

On a successful transition, the PR's URL is also attached as a link on the work item (Plane's
Links tab) — checked against existing links first, so repeat runs don't duplicate it. A
transition that would move a work item **backward** (e.g. a stale reopened PR on an
already-Done ticket) is refused, not silently applied.

## One-way, deliberately

Git → Plane only. Plane never writes back to git — no comments, no status checks, nothing.
This is the whole point: Plane's own GitHub integration (2-way issue/PR sync) is Pro-gated even
self-hosted, and a one-way flow removes both the paywall surface and any sync-loop risk. If a
work item's state needs correcting, correct it in Plane directly; this automation won't fight
you.

## How it runs

The logic lives in a standalone public repo,
[`thatkazuk1/plane-transition`](https://github.com/thatkazuk1/plane-transition) — not part of
this monorepo, deliberately, since it's a generic PR-to-Plane bridge with no homelab-specific
code. It's a small Python tool (official `plane-sdk`, pinned to an exact version) packaged as a
single container image on `ghcr.io`, wrapped in an `action.yml` so GitHub Actions can `uses:`
it directly. Forgejo Actions resolves the same external `uses:` the same way GitHub does —
confirmed live (2026-08-31) — so both `.github/workflows/plane-sync.yml` on
[`infra-stackdoc`](https://github.com/thatkazuk1/infra-stackdoc) and
`.forgejo/workflows/plane-sync.yml` here use the identical `uses: thatkazuk1/plane-transition@v1`
form. The action's `runs.image` is itself pinned to the published image's immutable digest, so
that floating `v1` tag always resolves to a known-good container regardless of what's on
`plane-transition`'s default branch at the time.

Each repo's workflow has two jobs, gated on `github.event.action`:

```yaml
jobs:
  start:
    if: github.event.action == 'opened' || github.event.action == 'reopened'
    # ...target-state: started, keywords: start,starts,started
  transition:
    if: github.event.action == 'closed' && github.event.pull_request.merged == true
    # ...target-state: Done (default keywords)
```

Both jobs pass `${{ github.event.pull_request.title }}` + `.body` as the text to scan, and
`${{ github.event.pull_request.html_url }}` as the PR link to attach.

## Where the token lives

A **workspace-scoped** Plane API token (created in Plane UI → Workspace Settings → API
Tokens), stored as the plain repo secret `PLANE_API_TOKEN` in each consumer repo — GitHub repo
secret on `infra-stackdoc`, Forgejo repo secret here. This follows the fleet's established CI
secret pattern (plain repo secrets, e.g. `KOMODO_API_KEY`), not `secrets.enc.env`/SOPS, since
this token belongs to Plane's CI surface, not this repo's deploy pipeline.

**Blast radius:** the token can edit or delete every work item in the `shokunbi` workspace,
across every project. Mitigations: the tool never logs it (verified — no `--dry-run` dump, no
`HttpError` header dump, nothing in any commit or report); GitHub/Forgejo mask secrets in logs
by default. Residual risk accepted, matching this fleet's non-rotation posture for other
long-lived credentials.

**Mirror double-fire:** this workflow file also lands on `thatkazuk1/homelab` (this repo's
GitHub push mirror). It has no `PLANE_API_TOKEN` secret configured, so if Actions ever runs
there, `plane-transition` prints `no token, skipping` and exits 0 — a deliberate design choice
in the tool itself, not a workaround bolted on here.

## Known limitation: keyword false positives

The tool does plain keyword + regex matching, not NLP — it doesn't understand PR-writing
context. Writing `Closes HOMELAB-42` anywhere in a PR's title or body triggers the transition
when that PR merges, even if you were just describing a future step rather than actually
closing it. This isn't hypothetical: it happened during this feature's own live verification
(2026-08-31) — a verification PR's body mentioned "Closes HOMELABSTA-19" as instructions for a
follow-up step, and the ticket transitioned a PR earlier than planned. Accepted risk at this
scale; keep closing-keyword phrasing intentional in PR text.

## Extending to another project or repo

No change needed in `plane-transition` itself — `identifier-prefixes`, `target-state`,
`keywords`, and `pr-url` are all per-workflow config. Add a `plane-sync.yml` (or
`.forgejo/workflows/` equivalent) to the new repo, following the two-job shape above, pointed at
the new Plane project's identifier prefix and a `PLANE_API_TOKEN` secret. See
[`plane-transition`'s README](https://github.com/thatkazuk1/plane-transition#readme) for the
full input reference.

## Not built

- **PR closed unmerged → revert.** The mirror of the "opened → In Progress" trigger — if a PR
  that started a work item gets closed without merging, nothing currently moves it back. Not
  requested yet.
- **Cycle, module, or assignee automation.** Out of scope by design — this only moves state.
