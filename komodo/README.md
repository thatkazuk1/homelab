# komodo/

**Status:** Komodo is live and is the fleet's GitOps orchestrator (Komodo Core on
`komodo-prod-01`, Periphery agents across the standard fleet). This is not a stale
placeholder — see `CLAUDE.md` and `handbook/docs/operations/deploy-triggers.md` for the
current deploy pipeline.

This directory is currently unused. The original plan (ADR-0002) was for Komodo's own
configuration ("Resource Syncs") to live here as version-controlled TOML, with a repo-level
`ResourceSync` driving fleet-wide redeploys from that TOML. That mechanism was evaluated
(Sprint 3p) and rejected — an open upstream bug (`moghtech/komodo#1120`) meant its `deploy:
true` didn't reliably fire. The fleet instead uses a Komodo `Procedure`
(`deploy-all-changed`, one `Batch Deploy Stack If Changed` stage targeting `*`), configured
directly in the Komodo UI rather than as committed TOML — see ADR-0015 for the decision and
`handbook/docs/operations/deploy-triggers.md` for how it works day to day.

Every Stack's own definition lives under `stacks/<name>/` (ADR-0009), not here. If this
fleet later adopts Komodo's TOML-based Resource Sync for real (e.g. if the upstream bug is
fixed and the tradeoffs change), this is where that configuration would go.
