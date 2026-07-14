## Admin panel access

Vaultwarden's `ADMIN_TOKEN` environment variable is deliberately unset.
The `/admin` backend UI is not exposed on this instance. Rationale:
the admin panel is a real attack surface, and this fleet does not
require it for normal operation. If admin access is ever needed
(user management, DB inspection, etc.), the token can be set
temporarily and removed after use rather than left configured
permanently.
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
