# ADR-0015: Handbook source location and internal-only serving

## Status

Accepted — 2026-07-09. Amended 2026-07-10 to reflect the serving architecture actually
implemented, which diverged from this ADR's original text.

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
- **Build:** a CI pipeline builds the MkDocs Material source into a static site, packaged as
  an nginx image, pushed to this homelab's own container registry.
- **Serve:** the image is deployed as a Komodo Stack, reachable directly via a bare port
  exposure on its host — **not** fronted by the fleet's central reverse proxy. An internal DNS
  rewrite points the handbook's `.lan` hostname straight at that host. No Cloudflare Tunnel,
  no Tailscale, no public URL.

  **The central reverse proxy was considered and bypassed.** Its primary HTTP entrypoint
  carries an unconditional HTTP→HTTPS redirect, applied fleet-wide with no per-router
  opt-out. Every existing router on that instance uses the TLS entrypoint with
  Cloudflare-issued certificates — there was no precedent for a plain-HTTP LAN-only route.
  Adding a new non-redirecting entrypoint to accommodate one LAN-only wiki would require
  editing the proxy's static configuration and restarting it — a blast radius covering every
  routed service in the fleet. Not justified for this stack. Direct port exposure was chosen
  instead.

  If the handbook ever needs a different serving profile (public URL, TLS, a clean hostname
  without a port), the lower-risk path is migrating the stack to the platform already serving
  comparable public-facing workloads, rather than reverse-proxy surgery on shared
  infrastructure.

## Reasoning

- **Clean separation from private working notes.** `handbook/` is deliberately a sibling of
  the operator's private notes directory, not a subdirectory of it — content meant to be read
  by a stranger lives apart from operator working notes, structurally, not just by a
  `.gitignore` line.
- **Same GitOps pipeline as everything else.** The handbook is just another CI-built,
  Komodo-deployed, git-driven stack. No bespoke publishing mechanism, no second deployment
  story to maintain.
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

## Consequences

- New infrastructure: a CI runner (meta-infrastructure, not itself Komodo-managed, matching
  the precedent set by other bootstrap-circular meta-infrastructure), a build workflow, a
  Komodo Stack with automatic updates enabled for fast content iteration, and an internal DNS
  rewrite.
- The URL includes a port. This is intentional, a direct consequence of bypassing the central
  reverse proxy, not an oversight to fix.
- When public serving is eventually wanted, the additive path is a platform migration rather
  than a reverse-proxy route on shared infrastructure — a deliberate change from this ADR's
  original plan, made to avoid a shared-infrastructure restart risk a second time.
- The handbook's content is public from the moment it's pushed, even though nothing serves it
  publicly yet — anyone cloning the GitHub mirror can read it. This is accepted, not an
  oversight: the content itself isn't sensitive; only the serving surface is deliberately not
  yet public.

## Alternatives considered

- **A static-hosting platform tied to the code host (e.g. GitHub Pages).** Rejected — forks
  the deployment pattern into a mechanism that bypasses the Git-to-Komodo pipeline this whole
  project is built around.
- **A CDN-native static hosting product.** Rejected for the same reason: a second, parallel
  deployment mechanism outside GitOps.
- **Serve via the platform already hosting non-Komodo-managed workloads.** Rejected at this
  stage — that platform already sits outside the reconciliation model used everywhere else;
  adding the handbook there would compound rather than resolve that tension.
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

---

_Source ADR authored during Sprint 3d, amended Sprint 3e. Public version adapted for this
handbook; the internal record lives in the operator's private notes._
