# Operations: Maintaining the handbook

This handbook is itself a Komodo-managed stack, built through the same GitOps pipeline as
everything else in the fleet. This page covers how to edit it, publish it, and keep it
honest.

## Source location

The handbook's source lives at `handbook/` in the monorepo (self-hosted at Forgejo, mirrored
to GitHub as `kazuki/homelab`) — a sibling of `stacks/`, not nested inside it. It's tracked
and public from the moment it's pushed, same as the rest of the shareable repo content.

## Authoring workflow

1. Edit any `.md` file under `handbook/docs/`.
2. `git commit`, `git push`.
3. Forgejo Actions picks up the push, builds a new MkDocs Material site, packages it as an
   nginx image, and pushes it to Forgejo's own container registry.
4. Komodo pulls the new image and redeploys the running `handbook` container.

Steps 3 and 4 are automated in principle — that's the whole point of the pipeline — but see
the next section for the current honest state of step 4.

## Auto-trigger reality

**As of writing, Komodo's automatic redeploy triggers are not reliable.** Both the webhook
path and Komodo's own Auto Update polling have failed to redeploy a freshly-built image
within a reasonable window in recent sprints. The working fallback: **Komodo UI → the
`handbook` Stack → Deploy**, which applies the latest built image immediately. Treat this as
the normal step after a push, not a break-glass fallback — a dedicated investigation into why
the automatic triggers aren't firing is a known, not-yet-scheduled carryover.

Step 3 (the Forgejo Actions build+push) has been fast and consistently automatic in practice
(under a minute); it's specifically step 4 (Komodo picking up the new image) that currently
needs a manual nudge.

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
