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
- **Not yet deployed or adopted.** `default.toml` has the `[[stack]]` block; nothing has been
  pushed, and no consumer points at this yet.
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
