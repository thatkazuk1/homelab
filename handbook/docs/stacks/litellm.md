# litellm

LiteLLM proxy — a single OpenAI-compatible endpoint in front of the fleet's Ollama hosts (ollama-prod-01, nexus-v), so consumers (Sure, SparkyFitness) stop hardcoding a backend URL. Backed by its own Postgres for the Admin UI (/ui — login, virtual keys, spend/request history). Model routing itself stays in config.yaml, not the database (STORE_MODEL_IN_DB deliberately unset), so git remains the source of truth for what's routed where — the DB only backs UI/key/usage state.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-02` |
| Category | ai-gateway |
| Status | new |
| Repo path | [`stacks/litellm/`](https://github.com/meetKazuki/homelab/tree/master/stacks/litellm) |

## Services

### `litellm-db`

- **Image:** `postgres:18.3-alpine`
- **Container:** `litellm-db`
- **Restart policy:** `unless-stopped`

### `litellm`

- **Image:** `ghcr.io/berriai/litellm:v1.83.14-stable`
- **Container:** `litellm`
- **Restart policy:** `unless-stopped`
- **Ports:** `4000:4000`

## Named volumes

- `litellm-db-data`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/litellm/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

- Exists to give Sure/SparkyFitness one URL instead of each hardcoding an Ollama backend, and
  to make the "laptop can be off/asleep" tolerance automatic (cooldown + priority failover)
  instead of per-consumer retry logic. Session context: `docker-prod-02` was chosen by the
  operator directly, not derived from a requirement.
- **GPUStack was considered first and rejected** — it looked like the better fit (a real fleet
  orchestrator, not just a gateway) until checking its own docs: workers are Linux-only (no
  Windows/WSL2), and its NVIDIA backends are vLLM/SGLang/VoxBox with no GGUF/llama.cpp support.
  Fails on both fronts here — `ollama-prod-01` has to stay Windows-native (no Docker, for GPU
  access), and the `qwen3-vl` models are GGUF, which vLLM/SGLang don't load. LiteLLM (a gateway
  in front of the existing Ollama servers, not a replacement for them) is the fit instead.
- Image tag `v1.83.14-stable` was confirmed live against the GHCR registry (anonymous manifest
  pull, 200), not assumed — LiteLLM's own docs example used a different, newer tag
  (`v1.90.2`) that wasn't independently checked, so the pinned tag here is the one actually
  verified to exist, not necessarily the newest.
- **Deliberately stateless, one backend, no fallback yet** (minimal footprint over full
  build-out — see the operator's standing preference for this). `config.yaml` only routes
  `vision-default` to `ollama-prod-01`, matching what SparkyFitness already points at directly,
  so switching SparkyFitness to this proxy should be a no-op change in its AI Services URL, not
  a behavior change.
- No Postgres DB, so no per-consumer virtual keys and no spend/usage history — every consumer
  shares the one `LITELLM_MASTER_KEY`. Revisit if usage tracking or key-scoping per consumer
  becomes worth the extra stack.
- **The `nexus-v` fallback tier is written but commented out in `config.yaml`, on purpose.**
  Two unresolved problems before it should be enabled:
  1. `nexus-v` only has `qwen2.5vl:7b` pulled, not `qwen3-vl:4b-instruct` — it would be a
     different model under the same `model_name`, not a clean swap. Verify output is
     acceptable to every consumer (or pull the matching model onto `nexus-v`) first.
  2. `nexus-v`'s LAN IP (`192.168.30.108`) has no DHCP reservation, unlike
     `ollama-prod-01`'s (`192.168.30.111`). It can change. Get one from the operator (OPNsense)
     before relying on this in the config rather than re-diagnosing it later.
- **Network check done before wiring the fallback address (2026-09-23):** `docker-prod-02` has
  no tailnet at all (no `tailscale` binary, confirmed via SSH) — `nexus-v`'s tailnet IP
  (`100.73.5.121`) is unreachable from here, same constraint as `ollama-prod-01`'s tailnet IP
  being unreachable from `docker-prod-02` (see the `ollama-prod-01` CLAUDE.md quirks entry).
  `nexus-v`'s LAN IP (`192.168.30.108`) *is* reachable from `docker-prod-02` (confirmed live,
  http 200) — same Wi-Fi subnet as `ollama-prod-01`. Use the LAN IP if the fallback is ever
  enabled, never the tailnet one.
- `LITELLM_MASTER_KEY` was minted here (not supplied by the operator — it's a token this
  gateway checks against, not an external credential) via `openssl rand -hex 32`, prefixed
  `sk-`. Encrypted with `sops --encrypt`, round-trip verified (`diff -q` clean, sha256 match on
  both sides), scratch plaintext shredded immediately. Never printed.
- Deployed 2026-09-23. First deploy hit a real stall (`docker compose pull` sat at flat network
  I/O for ~7 minutes with zero logs on either side) — turned out to be the pull's final
  extraction/checksum phase reading as idle, not an actual hang; a direct `docker pull` on the
  host confirmed the image was already fully fetched and the stack came up clean right after.
- **Postgres added 2026-09-23** so `/ui` works (it requires a DB connection to function at all,
  confirmed against LiteLLM's own docs — there's no degraded no-DB login mode). `STORE_MODEL_IN_DB`
  deliberately left unset — the DB only backs UI/key/session/history state, not model routing,
  so `config.yaml` stays the single source of truth and nothing can drift from git via the UI.
  **Mistake caught, not a handoff fabrication this time — my own:** the first attempt mounted
  `litellm-db-data:/var/lib/postgresql/data`, copied from an older stack's pattern without
  checking `sparkyfitness`'s own `postgres:18.3-alpine` service first. Postgres 18's official
  image expects a mount at `/var/lib/postgresql` (no `/data` suffix) and refuses to start
  against the old path — `litellm-db` crash-looped immediately, `litellm` never got past
  `Created` (blocked on `depends_on: service_healthy`). Confirmed the volume was still empty
  (crashed before ever writing anything) before fixing the path and redeploying, no data at
  risk. If this stack is ever copied as a template, check the target Postgres major version's
  expected mount path — it changed between 17 and 18, this repo now has stacks straddling both.
- Follow-ups, in order, once the operator wants to proceed:
  1. Push and verify the Stack deploys clean (`docker logs litellm`, then
     `curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://192.168.50.100:4000/health/liveliness`
     via `sops exec-env` so the key is never printed).
  2. Repoint SparkyFitness's AI Services URL from `http://192.168.30.111:11434` to
     `http://192.168.50.100:4000` (model name `vision-default`, API key = the master key) and
     confirm a real photo scan still works.
  3. Actually test the failover mechanism before trusting it in production — stop
     `ollama-prod-01`'s Ollama service (or block the port) and confirm the proxy behaves
     sensibly (error vs. hang), *before* the fallback tier is ever enabled for real.
  4. Once Sure comes off Azure Foundry (temporary per the operator), decide whether it also
     routes through this proxy or keeps a direct backend — not decided yet.

---

*This page is auto-generated from `stacks/litellm/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/litellm/notes.md`.*
