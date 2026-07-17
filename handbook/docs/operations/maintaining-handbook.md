# Operations: Maintaining the handbook

This handbook is a Coolify tenant on `coolify-prod-01`, built directly from the fleet
monorepo's `handbook/` subdirectory — see **Architecture → Coolify** for how that pipeline
works in general. This page covers how to edit it, publish it, and keep it honest.

## Source location

The handbook's source lives at `handbook/` in the monorepo (self-hosted at Forgejo, mirrored
to GitHub as `meetKazuki/homelab`) — a sibling of `stacks/`, not nested inside it. It's tracked
and public from the moment it's pushed, same as the rest of the shareable repo content.

## Authoring workflow

1. Edit any `.md` file under `handbook/docs/`.
2. `git commit`, `git push` (to the Forgejo origin — the canonical repo).
3. Forgejo's push mirror syncs the change to the GitHub mirror. This is not instant — there's
   a real, occasionally multi-commit lag window, not a push-triggered sync. If a change needs
   to land immediately, trigger it manually: Forgejo → repo **Settings → Push Mirrors →
   Synchronize Now**.
4. In Coolify's UI, open the `handbook` application and click **Deploy**. Coolify pulls the
   current GitHub mirror state, rebuilds the `Base Directory: /handbook` Dockerfile, and
   rolls the new container out.

Step 4 is manual — see the next section.

## Auto-trigger reality

**Coolify has no auto-deploy webhook configured for this application.** A push (even after
the mirror has synced) does not trigger a rebuild by itself; the **Deploy** button in Coolify's
UI is the actual publish step, every time. Treat it as the normal step after a push, not a
break-glass fallback. This is the same operational shape the pipeline had before the Sprint 3k
migration to Coolify — a webhook could close this gap in the future, but it isn't configured
today, and setting one up wasn't part of the migration itself.

A full rebuild currently takes several minutes (the `mkdocs-material` pip install is the slow
step; Docker layer caching should make it much faster on repeat deploys unless the Coolify
build environment doesn't preserve cache between deploys — not yet confirmed either way).
Content-only changes and layout/theme changes both go through the same rebuild; there's no
separate fast path for one over the other.

## Local preview

Build and run the site locally before pushing, to catch layout or content problems early:

```bash
cd handbook
docker build -t handbook-preview .
docker run --rm -d -p 8888:80 handbook-preview
```

Then open `http://localhost:8888/`. The build uses `mkdocs build --strict` internally — any
broken internal link or markdown warning fails the build outright, both locally and in CI, so
a successful local build is a real signal the push will go green.

## Style basics

The site is built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).
A few extensions are already enabled in `mkdocs.yml`:

- **Admonitions** — `!!! note`, `!!! warning`, etc., for callouts.
- **Code fences with language tags** — for syntax highlighting.
- **Tables** — standard GitHub-flavored markdown tables.
- **Inline links** — relative links between pages (`[text](../other-page.md)`) are checked by
  the strict build, so a typo'd link fails the build rather than silently 404ing in
  production.

Material's own documentation covers the full extension set if a page needs something beyond
these basics.

## Content principles

- **Accurate over aspirational.** Document what actually is, not what should eventually be
  true. The "Auto-trigger reality" section above is the clearest example — it would be easy
  to describe the pipeline as fully automatic and quietly wrong; it isn't, so it says so.
- **Reasoning matters as much as steps.** A page that just lists commands is thinner than one
  that explains why those commands and not some other approach — that's most of what
  separates this handbook from a bare command reference.
- **Brevity where possible.** Say what's needed, skip what isn't. Length targets in this
  handbook are guidelines, not gates.

## Adding a page

1. Create the `.md` file under the appropriate `handbook/docs/` subdirectory.
2. Add it to the `nav:` block in `handbook/mkdocs.yml` — this controls both whether it appears
   in the sidebar at all, and where.
3. Commit and push as usual.

Nav order in `mkdocs.yml` directly controls sidebar order — there's no separate ordering
mechanism.

## Generated stack pages

`handbook/docs/stacks/*.md` pages — except the hand-authored `index.md` — are auto-generated
from `stacks/*/compose.yml` or `stacks/*/compose.<host>.yml` (Sprint 3o, extended for
multi-file stacks and full lifecycle management in Sprint 3t). This is the first piece of
Goal 1's "living documentation" property: the compose file is the source of truth for a
stack's reference content, not a hand-written page that can silently drift from it. As of
Sprint 3t the generator handles the full stack lifecycle — adding a stack directory produces
a page and a nav entry on the next run; removing one prunes both. No manual `mkdocs.yml`
editing or page deletion is needed either way.

### Single-file vs. multi-file stacks

A stack directory is one of two shapes:

- **Single-file:** `stacks/<name>/compose.yml`. One host, one page.
- **Multi-file:** `stacks/<name>/compose.<host>.yml`, one or more, no `compose.yml`. Used
  where the same logical stack has real per-host divergence (`komodo-periphery`, `hawser`) —
  see ADR-0011 and Sprint 3i's periphery audit. Still one page per stack, not per host: the
  page carries a "Deployed on" section listing every host with a link to its own compose
  file, and the "Services" reference content is sourced from the alphabetically-first file
  (per-host drift in fields the template doesn't render, like environment variables, is
  intentionally not surfaced on the page — check the linked file for that).

A directory with **both** `compose.yml` and `compose.<host>.yml` files is ambiguous; the
generator logs an error and skips it rather than guessing.

### The `x-meta:` block

Every stack the generator handles carries an `x-meta:` key at the top of its compose file (or,
for multi-file stacks, each `compose.<host>.yml`) — a Compose extension key (`x-*`), ignored
by Compose itself at deploy time, that holds the generator's metadata:

```yaml
x-meta:
  name: homepage
  host: docker-prod-01
  category: dashboard
  description: >
    A single-page dashboard showing the state of every service in the homelab.
  status: adopted            # adopted | meta-infra | manual
  adrs:
    - 10
  public_url: home.ts.kazuki.uk   # optional
  internal_url:                   # optional
```

For multi-file stacks, each per-host file's `x-meta.name` is host-suffixed (e.g.
`hawser-core-01`) so the file is self-describing on its own — but the generator overrides
`name` with the stack **directory** name when rendering the page, since it's one page per
directory, not per host. The alphabetically-first file's other `x-meta` fields (description,
category, status, adrs) are used as the shared/canonical values for the page.

`adrs:` numbers that don't have a corresponding page under `handbook/docs/decisions/` render
as plain text instead of a broken link — not every ADR in `docs/adrs/` is published to the
public handbook.

### Per-stack operational notes

`stacks/<name>/notes.md` is optional, hand-written, and holds what the generator can't derive
from the compose file: quirks, lessons learned, migration history, specific caveats. It's
composed into the generated page's "Operational notes" section verbatim. Reference-level facts
(host, image, ports, secrets pattern, category, ADRs) belong in the compose file or `x-meta:`,
not here — if it's already on the reference table, it doesn't need repeating in notes.

### Regenerating

```bash
python3 scripts/generate-stack-pages.py
```

Reads every `stacks/<name>/compose.yml` or `stacks/<name>/compose.<host>.yml`, renders
`scripts/templates/stack-page.md.j2`, writes `handbook/docs/stacks/<name>.md`, prunes any
`handbook/docs/stacks/*.md` page with no corresponding stack directory (except the
hand-authored `index.md`), and rewrites `handbook/mkdocs.yml`'s `nav.Stacks` section to match
the current stack list — alphabetical, `Overview` first. Requires `jinja2`, `PyYAML`, and
`ruamel.yaml` (`pip install jinja2 pyyaml ruamel.yaml`; the last one is needed for the
mkdocs.yml roundtrip, since it preserves comments and formatting elsewhere in the file that a
plain PyYAML dump would drop). **Never edit a generated page, or the `Stacks` nav section, by
hand** — the next regeneration overwrites both. Fix the compose file's `x-meta:`, the
per-stack `notes.md`, or the template instead.

One stack is currently out of scope for the generator, deliberately: `coolify` has no
`compose.yml` or `compose.<host>.yml` (three separately-named compose files — `proxy.`,
`source.`, `source.prod.`-prefixed — and it's outside Komodo/git management by design, see
**Architecture → Coolify**).

### Pre-commit hook

A git hook regenerates affected pages automatically when a staged commit touches a stack's
`compose.yml`, `compose.<host>.yml`, or `notes.md`, and stages the regenerated output
(including page deletions from orphan pruning) and the updated `mkdocs.yml` alongside. Git
hooks aren't tracked in the repo, so install it once after cloning:

```bash
./scripts/install-hooks.sh
```

This copies the tracked `scripts/hooks/pre-commit` into `.git/hooks/pre-commit`.

### CI safety net

`.forgejo/workflows/check-generated-pages.yml` runs on every push touching a stack's
`compose.yml`/`compose.<host>.yml`/`notes.md`, the generator, its templates,
`handbook/docs/stacks/**`, or `handbook/mkdocs.yml`. It regenerates the pages and nav and
fails the build (`git diff --exit-code` against both `handbook/docs/stacks/` and
`handbook/mkdocs.yml`) if the result doesn't match what was committed — a backstop for anyone
who pushes without the pre-commit hook installed. The job's default container (`docker:27-cli`)
has git but neither Python nor Node.js, so the workflow installs `python3`/`pip` via `apk`
(including `ruamel.yaml`) and does its own manual git checkout with the runner's injected
`GITHUB_TOKEN` rather than the JS-based `actions/checkout` action.

### Adding or removing a stack

**Adding:** create `stacks/<name>/compose.yml` (or one or more `compose.<host>.yml` files) with
an `x-meta:` block in at least the alphabetically-first file, optionally add
`stacks/<name>/notes.md`, then run the generator (or just commit — the pre-commit hook does it
for you). The page and nav entry appear automatically; no `mkdocs.yml` editing needed.

**Removing:** delete the `stacks/<name>/` directory, run the generator (or commit — the hook
handles it). The page and nav entry disappear automatically.
