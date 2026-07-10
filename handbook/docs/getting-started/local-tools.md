# Getting Started: Local tools

What you need on a workstation to actually work on this repo — cloning it, editing secrets,
previewing the handbook, pushing changes. The operator's own workstation (`nexus-v`) runs all
of this; any equivalent Linux/macOS machine works the same way.

## SSH client

Needed to reach any fleet host directly. Present by default on Linux and macOS. See
[Getting Started: SSH](ssh.md) for the per-host key setup and `~/.ssh/config` structure this
repo expects.

## `sops` and `age`

Needed to read or edit any stack's secrets. Both are single static binaries, no package
manager required. See [Getting Started: SOPS and age](sops.md) for install links and the full
encrypt/decrypt/edit workflow.

Worth repeating here because it's easy to miss: you do **not** need either binary just to
*deploy* a stack — Komodo's Periphery agents carry their own copies inside the custom
`komodo-periphery-sops` image. You only need them locally to read or change a secret file
yourself.

## `git`

The whole repo is the source of truth; every change here flows through a commit and a push
to Forgejo. Present by default on Linux and macOS, or via your platform's usual package
manager.

## `docker`

Needed for one specific thing: previewing the handbook locally before pushing, using the same
`mkdocs build --strict` process CI runs. See
[Operations: Maintaining the handbook](../operations/maintaining-handbook.md) for the exact
build/run commands. Not needed for anything else on a workstation — no stack is ever built or
run locally as part of the normal GitOps flow; that's what Periphery agents are for.

## Optional: `mkdocs-material` installed directly

If you're iterating on handbook content frequently, running MkDocs' own dev server
(`mkdocs serve`) with `mkdocs-material` installed via `pip`/`uv` gives live-reload on save —
faster than a full Docker build-and-run cycle for a quick wording check. Not required; the
Docker path is the one CI actually exercises, so it's the one that matters for confirming a
push will go green. Treat a local `mkdocs serve` as a fast draft loop, and the Docker build
as the final check before pushing.

## What you don't need

No Komodo API key, no Forgejo access token — day-to-day work on this repo doesn't require
either. Komodo Stack creation and Forgejo webhook registration are operator-performed UI
actions (see [ADR-0013](../decisions/index.md)), not something a workstation's own tooling
needs credentials for.
