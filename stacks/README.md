# stacks/

Docker Compose stacks, organized flat by service — `stacks/<name>/compose.yml` — **not**
nested by host. See ADR-0009 for the reasoning: a Komodo Stack's host binding lives in its
mutable `Server` field, not in the git path, so nesting by host would imply a coupling that
doesn't reflect Komodo's data model.

Where a stack's compose genuinely diverges per host (not just its Komodo `Server`
assignment, but real content differences — e.g. `komodo-periphery`, whose mount paths differ
by host), the host goes in the *filename*, not a directory level:
`stacks/<name>/compose.<host>.yml`.

Each stack directory may also carry:
- `secrets.enc.env` — the stack's SOPS-encrypted secrets, if it has any (ADR-0008)
- a stack-specific `README.md`

Stack pages in the handbook and the `Stacks` nav are generated from this directory by
`scripts/generate-stack-pages.py` — adding or removing a `stacks/<name>/` directory and
committing is sufficient; no manual page or nav editing.
