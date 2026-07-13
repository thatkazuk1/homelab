- Uses YAML anchors (`x-db-env`, `x-rails-env`) for shared environment blocks — kept as-is
  during adoption rather than rewritten to the bare-pass-through style most other stacks use;
  both work identically with the `sops exec-env` wrapper, and rewriting a working production
  compose structure for stylistic uniformity wasn't worth the risk.
- Two vars present in the original host `.env` (`SECRET_KEY_BASE_II`, `OPENAI_ACCESS_TOKEN`)
  were confirmed unreferenced anywhere in the compose file and dropped, per operator
  confirmation — still an open question whether that silently disables a Sure feature, or
  whether they were just template leftovers.
- A mandatory backup was taken and verified off-host *before* any adoption work touched this
  stack, given the data sensitivity — the strictest pre-flight discipline applied to any
  adoption to date.
- Functional verification exceeded the usual bar: real, live operator browser traffic against
  the redeployed stack (actual 200s on `/transactions`), not just a health-check response.
- Redis runs with no password configured at all in this deployment — a real characteristic of
  the current setup, not a gap introduced by adoption.
- This stack is the origin case for the "never dump a full secret-bearing structure during
  verification" discipline now in `CLAUDE.md` — an early verification step here used an
  unfiltered container-environment dump instead of a targeted grep, which is exactly the
  mistake that rule exists to prevent.
