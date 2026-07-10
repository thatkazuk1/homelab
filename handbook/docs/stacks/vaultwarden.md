# vaultwarden

A self-hosted, Bitwarden-compatible password vault.

**Host:** `docker-prod-01`
**Access:** port `8000` on the host, domain configured via the secret `DOMAIN` var (not
reproduced here)
**Repo:** [`stacks/vaultwarden/`](https://github.com/meetKazuki/homelab/tree/master/stacks/vaultwarden)

## What it does

Vaultwarden is a lightweight, unofficial Bitwarden server implementation — same client apps,
same sync protocol, self-hosted backend. It holds the fleet's actual password data, which
makes it one of the two or three highest-stakes stacks in the whole repo from a
what-happens-if-this-goes-wrong standpoint (alongside `sure`, `garage`'s admin credentials).

## Configuration

- **Compose:** single-service, `vaultwarden/server:latest`
- **Secrets:** ADR-0010 pattern — `secrets.enc.env` with 5 vars: `PUID`, `PGID`, `TZ`,
  `DOMAIN`, `SIGNUPS_ALLOWED`. Notably, **no `ADMIN_TOKEN`** is present — whether that's
  deliberate hardening (admin panel disabled entirely) or an oversight from the original
  manual setup is an open question, not yet resolved.
- **Data:** bind mount, `/opt/homelab/vaultwarden/data:/data` — the vault database itself.
  No named Docker volume involved.

## Notable

- Adopted in Sprint 3b.1 with the strictest verification of that sprint's three stacks: a
  pre-adoption backup (both a tarball and an operator-captured native Vaultwarden export),
  and a forced redeploy confirmed via an authenticated vault-entry check rather than just a
  health-check response.
- A shell-quoting bug in the Komodo Wrapper field was hit and fixed by the operator directly
  during setup — fixed, but never documented with a root cause, so if it recurs the diagnosis
  starts from scratch.
- The pre-stop backup tarball was deleted before its checksum comparison completed; the
  off-host copy was confirmed present by size only, not by hash. Low risk given the
  independent native export existed as a second artifact, but a real gap in that sprint's
  verification rigor worth naming honestly.

## See also

- [Adopting a stack](../operations/adopting-a-stack.md)
- [ADR-0010 Per-stack SOPS secrets](../decisions/0010-per-stack-sops-secrets.md)
