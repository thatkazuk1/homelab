# Runbooks

Per-host and per-tool operational guides — environment specifics, known quirks, and recovery
procedures. Unlike the rest of `docs/` (ADRs, sprint history, conventions — disk-only per
ADR-0010), runbooks live here in the handbook: they're how-to-run material, useful to anyone
operating this fleet.

| Runbook | Covers |
|---|---|
| [Proxmox cluster](pve-cluster.md) | The `pve-01`/`pve-02` cluster: recovery-boot order, storage, quirks, **adding a new guest** (template-clone + cloud-init + Ansible), adopting a guest under Ansible, and adding a bare-metal node. |
| [`core-01`](core-01.md) | Raspberry Pi 4 running Home Assistant — cloud-init management, accounts, host specifics. |
| [Backrest backup](backrest-backup.md) | The restic-to-Google-Drive backup on `docker-prod-01` — config, secrets, restore. |
| [Komodo Core restore](komodo-restore.md) | Restoring Komodo Core's database from backup. |

`nas-01` has a runbook too, kept operator-side only (`docs/runbooks/nas-01.md`) — it documents
host-specific access and hardening details that don't belong in the public mirror.

Update runbooks in place, here. Editing one is a tracked change that goes through CI and the
public mirror like any other handbook page.
