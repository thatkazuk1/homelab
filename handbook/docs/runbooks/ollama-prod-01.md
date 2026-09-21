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
| Model | `qwen3-vl:4b` (vision + text, ~3.3 GB download) |

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
| `OLLAMA_CONTEXT_LENGTH` | `8192` | Ollama defaults to 4096 and silently truncates longer input, which breaks the chatbot's tool definitions. 8192 (not 16384) leaves VRAM headroom on a 6 GB card. |
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
curl http://192.168.30.111:11434/api/pull -d '{"model":"qwen3-vl:4b"}'
```

Sizing rule for this box: a model has to fit in **6 GB of VRAM together with Windows and other
GPU apps** (about 1 GB is already taken by the desktop). About 4B parameters, or 7–8B at Q4
with short context, is the ceiling. Larger models (the 26–27B ones on `nexus-v`) spill into
system RAM and lose the GPU's speed advantage; run those on `nexus-v` instead.

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
- **First request after any restart is slow** (30–75 s: model load plus first image encode).
  Warm requests take about a second or two. Consumers with short timeouts may fail on the first
  call only.
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
| SparkyFitness (`docker-prod-02`) | Settings, AI Services: service type **Ollama**, URL `http://192.168.30.111:11434`, custom model name `qwen3-vl:4b`, chat tool set **Core** | Configured in the app UI and stored in its database (the API key field is unused for Ollama). Not in the compose file, so nothing to redeploy. |

Add new consumers here. Anything that uses this host should tolerate it being off.

## 9. Why this is not under GitOps

The fleet's automation (Komodo Periphery, the Ansible `docker`/`periphery`/`baseline` roles) is
Linux and Docker based. This host is a personal Windows machine running Ollama natively for
GPU access, so it is documented rather than reconciled. If it ever becomes permanent
infrastructure, the natural next step is an Ansible role using WinRM or SSH, which is not
built today.
