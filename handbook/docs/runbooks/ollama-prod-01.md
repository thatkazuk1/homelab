# `ollama-prod-01` Runbook

> **Node:** ASUS TUF Dash F15 laptop (Windows), adopted into the fleet as a small, GPU-backed
> LLM host
> **Purpose:** light LLM tasks for homelab integrations — currently SparkyFitness meal-photo
> scanning and chat
> **Not Komodo-managed.** Windows host; no Periphery, no Ansible role, no Stack. Configured by
> hand over SSH and documented here instead.

## 1. What it is, and why it's shaped this way

`ollama-prod-01` is a personal Windows laptop that now also serves models over the LAN with
[Ollama](https://ollama.com). It exists because the fleet's Proxmox nodes are CPU-only, and a
vision model on CPU takes tens of seconds per photo. On the laptop's RTX 3060 a warm request
answers in a couple of seconds.

It is **not** a server in the usual sense: it sleeps, travels, and can be switched off. Every
consumer has to fail gracefully when it is unreachable.

| Item | Value |
|---|---|
| Hostname (fleet) | `ollama-prod-01` (tool-identity name, like `garage-prod-01`) |
| Hostname (Windows) | `NeXus-IV` |
| OS | Windows, admin local account |
| GPU | NVIDIA GeForce RTX 3060 Laptop, **6 GB VRAM** |
| RAM | 40 GB |
| Network | Wi-Fi, `192.168.30.111` (DHCP reservation in OPNsense). Also on the tailnet. |
| API | `http://192.168.30.111:11434` (Ollama, no authentication) |
| Ollama | 0.34.x, per-user install (`%LOCALAPPDATA%\Programs\Ollama`), models in `D:\.ollama\models` |
| Model | `qwen3-vl:4b-instruct` (vision + text, ~3.1 GB, non-thinking). The original `qwen3-vl:4b` is a thinking-only model and is still on disk but unused, see section 7. |

Because Ollama has no authentication, the API is only exposed to the two LAN subnets by a
firewall rule (section 4). Never publish it beyond the LAN or the tailnet.

## 2. Access

SSH with a per-host key, matching the fleet convention (`~/.ssh/id_ed25519_ollama-prod-01`,
`Host ollama-prod-01` in `~/.ssh/config`, `IdentitiesOnly yes`).

The account is a Windows administrator, so its key lives in
`C:\ProgramData\ssh\administrators_authorized_keys`, **not** in the user's own
`.ssh\authorized_keys` (Windows ignores that one for admins). The file needs its permissions
reset to Administrators + SYSTEM only, or `sshd` silently rejects it:

```powershell
icacls "$env:ProgramData\ssh\administrators_authorized_keys" /inheritance:r /grant "Administrators:F" /grant "SYSTEM:F"
```

One-time setup, in an **Administrator** PowerShell on the laptop:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
New-NetFirewallRule -Name sshd-lan -DisplayName "OpenSSH (LAN only)" -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow -RemoteAddress 192.168.30.0/24,192.168.50.0/24 -Profile Any
# write the public key to administrators_authorized_keys, then fix its ACL (above)
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force
```

Sessions land in PowerShell. Quoting a multi-line script through `ssh host 'powershell -Command "..."'`
is fragile; feed a script on stdin instead:

```bash
ssh ollama-prod-01 'powershell -NoProfile -Command -' < script.ps1
```

## 3. Installing Ollama

**Do this from a normal PowerShell window on the laptop's desktop, not over SSH.**
`winget install` hangs indefinitely in an SSH session (it waits on a prompt it cannot show).

```powershell
winget install --id Ollama.Ollama -e --accept-package-agreements --accept-source-agreements
```

If the download is slow, download `OllamaSetup.exe` on another machine and copy it over the
LAN; the file is ~1.6 GB. The laptop's own Wi-Fi downloads were slow enough (tens of KB/s)
that this was worth knowing about, though model pulls later ran at several MB/s.

## 4. Configuration

All settings are **user-level environment variables**. Ollama reads them at start.

| Variable | Value | Why |
|---|---|---|
| `OLLAMA_HOST` | `0.0.0.0:11434` | Listen on the LAN. The default is loopback only. |
| `OLLAMA_CONTEXT_LENGTH` | `8192` | Ollama defaults to 4096 and silently truncates longer input, which breaks the chatbot's tool definitions. 8192 is the safe default on a 6 GB card; 10240 is the most that stays fully on the GPU (section 5a). Above that the model spills to CPU and generation gets about 9x slower. |
| `OLLAMA_KEEP_ALIVE` | `1h` | Default is 5 minutes. A cold model load plus first image encode takes 30–75 s, so keep it warm. |
| `OLLAMA_FLASH_ATTENTION` | `1` | Required for a quantised KV cache. |
| `OLLAMA_KV_CACHE_TYPE` | `q8_0` | Halves the context cache (1152 to 612 MiB at 8192 tokens), which is what lets the model fit entirely on the GPU. |

Set them once (Administrator or normal PowerShell, `User` scope):

```powershell
[Environment]::SetEnvironmentVariable('OLLAMA_HOST','0.0.0.0:11434','User')
[Environment]::SetEnvironmentVariable('OLLAMA_CONTEXT_LENGTH','8192','User')
[Environment]::SetEnvironmentVariable('OLLAMA_KEEP_ALIVE','1h','User')
[Environment]::SetEnvironmentVariable('OLLAMA_FLASH_ATTENTION','1','User')
[Environment]::SetEnvironmentVariable('OLLAMA_KV_CACHE_TYPE','q8_0','User')
```

Firewall, LAN only (Administrator PowerShell):

```powershell
New-NetFirewallRule -Name ollama-lan -DisplayName "Ollama (LAN only)" -Direction Inbound -Protocol TCP -LocalPort 11434 -Action Allow -RemoteAddress 192.168.30.0/24,192.168.50.0/24 -Profile Any
```

The installer does **not** open this port itself.

### Power

The laptop must stay awake while serving. On AC: sleep set to never
(`powercfg /change standby-timeout-ac 0`) and lid-close action set to "do nothing"
(`powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0`, then
`powercfg /setactive SCHEME_CURRENT`). The lid setting could not be read back over SSH, so
confirm it by closing the lid on AC and checking the API still answers.

## 5. Pulling a model

```bash
curl http://192.168.30.111:11434/api/pull -d '{"model":"qwen3-vl:4b-instruct"}'
```

Sizing rule for this box: a model has to fit in **6 GB of VRAM together with Windows and other
GPU apps** (about 1.6 GB is already taken by the desktop, measured). About 4B parameters, or
7–8B at Q4 with short context, is the ceiling. Larger models spill into system RAM and lose
the GPU's speed advantage. `nexus-v` has no discrete GPU (CPU inference only), so it is not a
faster alternative for large prompts either.

**Prefer non-thinking (`-instruct`) model variants for anything that calls tools or returns
JSON.** A thinking model spends hundreds to thousands of tokens reasoning before it answers,
which dominates latency and can exhaust the context. See 5a for measurements.

### 5a. Capacity measurements (2026-09-21, RTX 3060 Laptop 6 GB, flash attention + q8_0 KV)

VRAM against context, one model loaded:

| `num_ctx` | KV cache | Weights + cache on GPU | Spilled to RAM | Layers on GPU |
|---|---|---|---|---|
| 8192 | 612 MiB | 3404 / 3404 MiB | none | 37/37 |
| 10240 | 765 MiB | 3559 / 3559 MiB | none | 37/37 |
| 12288 | 918 MiB | 3596 / 4136 MiB | 540 MiB | 35/37 |
| 16384 | 1224 MiB | 3627 / 4466 MiB | 840 MiB | 32/37 |

- The KV cache costs about **77 MiB per 1000 tokens** of context (q8_0). Doubling it from 8k to
  16k costs about 1 GB, which is more than the card has free after Windows (about 0.95 GB).
- **The speed cliff is sharp.** Fully on GPU the model generates about 55 tokens/s; with layers
  spilled it drops to about 6 tokens/s. A 14k-token prompt at 16k context took 63–103 s.
- **`OLLAMA_NUM_PARALLEL` does not help here.** Each extra slot multiplies the context
  allocation, so two 8k slots are a 16k cache and spill. Keep one slot and make requests short.
  Requests are serialised, so a slow request delays every other consumer.
- **Oversized prompts are cut to about half the context, not to the full context.** With
  `num_ctx=8192` a 14k-token prompt is truncated to 4098 tokens (`truncating input prompt
  limit=4098` in the server log). Anything that needs its whole prompt, such as tool
  definitions, silently loses part of it.
- **Model load** from a warm disk cache takes 4–7 s. The 30–75 s first-call figure seen earlier
  included the first image encode on a cold cache.
- Same measurements, thinking versus non-thinking model:

| Workload | `qwen3-vl:4b` (thinking) | `qwen3-vl:4b-instruct` |
|---|---|---|
| Photo to JSON (Sparky-shaped request) | 15–18 s; valid JSON in 1 of 3 runs, others `{}` or empty | 1.1 s warm; valid JSON in 3 of 3 runs |
| One tool-calling turn | 17–20 s (about 800 thinking tokens) | 2.3 s |

Only models that report the `vision` capability (`ollama show <model>`) can read photos.
Model names are exact: `qwen3-vl:4b` is a lowercase **L**, and a typo (`qwen3-v1:4b`) surfaces
in consumers as a generic "AI service returned an error".

## 6. Verifying

From any LAN host (a reachability check from `docker-prod-02` is the one that matters for
SparkyFitness):

```bash
curl -s http://192.168.30.111:11434/api/version
curl -s http://192.168.30.111:11434/api/ps      # loaded model, context_length, size_vram vs size
```

Healthy means `size_vram` equals `size` (fully on the GPU) and `context_length` is 8192.
If `size_vram` is smaller than `size`, part of the model has spilled to CPU RAM and requests
will be noticeably slower.

To confirm Ollama actually picked up its environment, check the server log rather than trusting
the registry. On the laptop:

```powershell
Get-Content "$env:LOCALAPPDATA\Ollama\server.log" | Select-String 'server config' | Select-Object -Last 1
Get-Content "$env:LOCALAPPDATA\Ollama\server.log" -Tail 300 | Select-String 'offloaded|llama_kv_cache: size'
```

Expect `OLLAMA_FLASH_ATTENTION:true`, `OLLAMA_KV_CACHE_TYPE:q8_0`,
`offloaded 37/37 layers to GPU`, and a KV cache of `q8_0`.

## 7. Known quirks

- **Restarting Ollama from the tray can start it with a stale environment.** After changing a
  variable, quitting and reopening Ollama from the Start menu did not always pick it up — the
  registry had the new value, the running process did not. Restart it from a shell that first
  reloads the variables from the registry:

  ```powershell
  Get-Process "ollama app","ollama" -ErrorAction SilentlyContinue | Stop-Process -Force
  foreach ($n in 'OLLAMA_HOST','OLLAMA_CONTEXT_LENGTH','OLLAMA_KEEP_ALIVE','OLLAMA_FLASH_ATTENTION','OLLAMA_KV_CACHE_TYPE') { Set-Item "env:$n" ([Environment]::GetEnvironmentVariable($n,'User')) }
  Start-Process "$env:LOCALAPPDATA\Programs\Ollama\ollama app.exe"
  ```

  A sign-out and sign-in (or a reboot) also makes Windows reload them for everything launched
  normally. Always verify with the log check in section 6.
- **Ollama runs in the user's desktop session.** It starts at login, not at boot. If the
  laptop reboots and nobody logs in, the API is down.
- **First request after any restart is slow** (model load 4–7 s warm, up to 30–75 s with a cold
  disk cache, plus first image encode). Warm requests take about a second or two. Consumers with
  short timeouts may fail on the first call only. Consumers may also send their own
  `keep_alive` on each request (SparkyFitness sends `30m`), which overrides
  `OLLAMA_KEEP_ALIVE` for that load.
- **Avoid thinking-only models such as `qwen3-vl:4b`.** `think:false` is ignored for tool calls
  and returns empty content for JSON (`format:"json"`) requests, and the default thinking output
  makes JSON requests come back empty or as `{}`. SparkyFitness reports that as "AI service
  returned no content" / "The provider blocked this photo". There is no server-side switch to
  disable thinking, so use the `-instruct` tag.
- **Wi-Fi only, as observed.** The wired adapter had no link at adoption time. A DHCP
  reservation covers the Wi-Fi address; if it moves to Ethernet, reserve that adapter's MAC too
  and update every consumer's URL.
- **`docker-prod-02` is not on the tailnet.** Consumers there must use the LAN address; the
  laptop's Tailscale address is unreachable from that VM.
- **6 GB is tight.** The full `Full (all tools)` chat tool set in SparkyFitness is too heavy
  for a 4B model; use `Core`.

## 8. Consumers

| Consumer | Setting | Notes |
|---|---|---|
| SparkyFitness (`docker-prod-02`) | Settings, AI Services: service type **Ollama**, URL `http://192.168.30.111:11434`, custom model name `qwen3-vl:4b-instruct`, chat tool set **Core** | Configured in the app UI and stored in its database (the API key field is unused for Ollama). Not in the compose file, so nothing to redeploy. Its photo requests use native `/api/chat` with `format:"json"` and `num_ctx:8192`, which is why a thinking model fails here (section 7). |

**Former consumer: Sure.** Sure's builtin assistant ran here from 2026-09-21 and was moved to a
hosted model the same day. Its 35 tool definitions alone are about 13k tokens, well beyond the
8192-token context this card can serve at full speed (the prompt was truncated to 4098 tokens,
so the assistant answered from data it never received), and a 16k context spills to CPU (section
5a). This host is not a good fit for Sure's tool-heavy assistant unless the tool set is cut to
about 8 tools (about 4.5k tokens).

Add new consumers here. Anything that uses this host should tolerate it being off. Prefer
short, single-turn requests: they are queued behind each other on one slot.

## 9. Why this is not under GitOps

The fleet's automation (Komodo Periphery, the Ansible `docker`/`periphery`/`baseline` roles) is
Linux and Docker based. This host is a personal Windows machine running Ollama natively for
GPU access, so it is documented rather than reconciled. If it ever becomes permanent
infrastructure, the natural next step is an Ansible role using WinRM or SSH, which is not
built today.
