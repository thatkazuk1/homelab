# ADR-0015: Handbook source location and internal-only serving

## Status

Accepted — 2026-07-09. Amended 2026-07-10 to reflect the serving architecture actually
implemented, which diverged from this ADR's original text. Amended again 2026-07-11: serving
migrated from a directly-exposed port to a [Coolify](../architecture/coolify.md) tenant.

## Context

The living-wiki goal and the publish-publicly goal had both been deferred while the
monorepo's own migration work took priority. [ADR-0003](0003-mkdocs-material.md) committed to
MkDocs Material as the wiki's tooling, with implementation explicitly deferred to a later
sprint. A separate decision excluded the operator's private working notes (ADRs, runbooks,
sprint history) from the public GitHub mirror.

Building the actual documentation pipeline raised two questions neither of those decisions had
answered: where does the handbook's own source content live relative to the private/public
split, and how is the built site served? Both needed a decision before any scaffolding could
be written.

## Decision

- **Source:** `handbook/` at the repo root, tracked in git, mirrored to GitHub alongside
  `stacks/`.
- **Build:** Coolify's git integration pulls the `handbook/` subdirectory directly from the
  repo's GitHub mirror and builds it on its own host, using the same multi-stage Dockerfile
  written when the pipeline was first stood up. No separate CI build step remains for the
  handbook specifically — content-only iteration (edit a page, push) now goes straight through
  Coolify's own build pipeline.
- **Serve:** the handbook is a [Coolify](../architecture/coolify.md) tenant, served by
  Coolify's own reverse proxy at `http://handbook.lan/` — plain HTTP, no port, no
  TLS/certificate attempt. An internal DNS rewrite points the hostname straight at Coolify's
  host. No Cloudflare Tunnel, no Tailscale, no public URL, and no involvement from the fleet's
  central reverse proxy — consistent with how this homelab keeps Coolify tenants separate from
  the fleet's primary routing layer.

  **Earlier state, preserved as history, not erased:** the site was originally built by a CI
  pipeline and deployed as a directly-orchestrated container, reachable at
  `http://handbook.lan:8092/` via a bare port exposure — not fronted by any reverse proxy at
  all. The fleet's central reverse proxy carries an unconditional HTTP→HTTPS redirect applied
  everywhere, with no per-route opt-out; adding a non-redirecting route for one LAN-only wiki
  was judged not worth the blast radius of a shared-infrastructure config change and restart.
  That reasoning is why the original implementation chose bare port-exposure over reverse-proxy
  surgery, and why this ADR's original text named a future move to Coolify as the lower-risk
  path to a clean, portless URL — which is exactly what happened.

## Reasoning

- **Clean separation from private working notes.** `handbook/` is deliberately a sibling of
  the operator's private notes directory, not a subdirectory of it — content meant to be read
  by a stranger lives apart from operator working notes, structurally, not just by a
  `.gitignore` line.
- **Same git-driven pipeline as everything else.** The handbook is just another git-driven,
  automatically-built stack, whichever platform builds it. No bespoke publishing mechanism, no
  second deployment story to maintain.
- **Deliberate source-public / serving-private split.** The content is authored in the open
  from day one — anyone with repo access can read the Markdown, and it mirrors to GitHub like
  any other tracked directory. What's *not* decided yet is how it's presented to the public
  internet: fonts, domain, whether it's the front door of a larger public presentation or a
  secondary artifact. Serving stays internal-only until that design conversation happens, so
  the pipeline doesn't get built twice.
- **Public URL is coupled to a separate, not-yet-had conversation** about public presentation
  — not a technical blocker, a sequencing one. Building the internal loop first means later
  content and polish work has something real to write into and iterate against, without
  forcing the public-presentation decision prematurely.
- **The Coolify migration removes the reverse-proxy restart risk this ADR originally accepted,
  rather than living with it indefinitely.** Coolify runs its own reverse proxy independent of
  the fleet's central one, so a plain-HTTP `.lan` route there carries none of the fleet-wide
  blast radius the original decision was avoiding. This validates the Coolify path this ADR's
  original Alternatives section rejected — rejected at the time because Coolify sat outside
  this homelab's reconciliation model as undocumented drift; once it became a documented,
  deliberate operational standard (see [Architecture → Coolify](../architecture/coolify.md)),
  the original objection no longer applied.

## Consequences

- **No more CI build step or orchestrated-container deployment for the handbook.**
  Content-only iteration now goes through Coolify's own build pipeline instead. **Caveat found
  during the migration: Coolify has no auto-deploy webhook configured for this tenant** — a
  push does not trigger a rebuild by itself. A manual "Deploy" click in Coolify's UI is
  required per change, the same operational shape the prior pipeline had (its own
  auto-redeploy mechanism was never observed to fire reliably either). Not yet fixed; a real,
  standing carryover.
- **The fleet monorepo's GitHub mirror is a push mirror on some interval, not instant.** The
  first redeploy attempt under the new pipeline built stale content because GitHub was still a
  few commits behind the canonical repo at deploy time; a manual mirror sync was needed to
  catch it up. Worth remembering for anything that pulls from the GitHub mirror rather than the
  canonical repo directly — there's a real, occasionally multi-commit lag window.
- The URL no longer includes a port — `http://handbook.lan/`, not `http://handbook.lan:8092/`.
  Coolify's own reverse proxy absorbs the port behind `:80`, closing the gap this ADR's
  original text named as an accepted-but-not-preferred consequence of the port-exposure
  approach.
- `handbook/` content is public from the moment it's pushed, even though the serving surface
  (`http://handbook.lan/`) stays LAN-only. This is unchanged from the original decision: the
  content itself (homelab documentation) isn't sensitive; only the serving surface is
  deliberately not yet public.

## Alternatives considered

- **GitHub Pages.** Rejected — forks the deployment pattern into a GitHub-native mechanism
  that bypasses this project's own git-driven pipeline.
- **A CDN-native static hosting product.** Rejected for the same reason: a second, parallel
  deployment mechanism outside this repo's normal reconciliation model.
- **Serve via Coolify (considered early).** Rejected at the time because Coolify sat outside
  this homelab's reconciliation model as undocumented drift; adding the handbook there would
  have compounded that tension instead of resolving it. **Superseded later**, once Coolify
  became a documented, deliberate operational standard elsewhere in this repo, which removed
  the original objection — this is the alternative that was ultimately adopted, recorded here
  rather than deleted, since the original rejection's reasoning was correct for its time and
  the situation genuinely changed, not a mistake being corrected.
- **Tailscale-only serving.** Rejected for this stage — internal DNS already covers "reachable
  from inside the house"; routing through the tailnet adds complexity with no present payoff
  until there's an actual need to read the handbook from outside the LAN.
- **Exclude the handbook from the public mirror until serving is public.** Rejected. The
  content is inherently open (homelab documentation, not credentials or internal reasoning)
  even before there's a public URL pointed at it; holding it back would just delay the
  publish-publicly goal for no security benefit.
- **Central-reverse-proxy fronting with a new non-redirecting entrypoint.** Rejected due to
  restart blast radius and no operational benefit for internal-only serving (added on
  amendment, reflecting the decision actually made).
- **Preserving the original port-exposure serving approach.** Rejected as ongoing maintenance
  burden once Coolify became this homelab's standard for tenant-shaped workloads — running two
  parallel serving mechanisms for the same content had no benefit once the Coolify path was
  verified working.

---

_Source ADR authored during Sprint 3d, amended Sprint 3e and Sprint 3k. Public version adapted
for this handbook; the internal record lives in the operator's private notes._
