#!/usr/bin/env bash
# Fills answer.toml.tmpl with per-node values + the SOPS-sourced root
# password, on the trusted PVE node running prepare-iso. Never commit
# the file this writes.
#
# Prerequisite (not yet true on pve-01/pve-02 as of Sprint 4c — see
# README.md): sops + age installed, fleet age key at
# ~/.config/sops/age/keys.txt.
#
# Usage:
#   ./render-answer.sh <hostname> <mgmt-cidr> <disk-model-filter> <ssh-pubkey-file> [fqdn-domain] [out-file]
#
# Example:
#   ./render-answer.sh pve-03 192.168.50.12/24 'Samsung*' ~/.ssh/id_ed25519_pve03.pub pve3.home /tmp/answer.pve-03.toml

set -euo pipefail

if [ "$#" -lt 4 ]; then
  echo "Usage: $0 <hostname> <mgmt-cidr> <disk-model-filter> <ssh-pubkey-file> [fqdn-domain] [out-file]" >&2
  exit 1
fi

HOSTNAME_VAL="$1"
MGMT_CIDR="$2"
DISK_FILTER="$3"
SSH_PUBKEY_FILE="$4"
FQDN_DOMAIN="${5:-pve.home}"
OUT_FILE="${6:-/tmp/answer.${HOSTNAME_VAL}.toml}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="${SCRIPT_DIR}/answer.toml.tmpl"
SECRETS="${SCRIPT_DIR}/secrets.enc.env"

if [ ! -r "$SSH_PUBKEY_FILE" ]; then
  echo "SSH pubkey file not readable: $SSH_PUBKEY_FILE" >&2
  exit 1
fi
SSH_PUBKEY="$(cat "$SSH_PUBKEY_FILE")"

ROOT_PASSWORD="$(sops -d --extract '["PROXMOX_ROOT_PASSWORD"]' "$SECRETS")"

# Old bash's ${var//} with a literal replacement is safe here since none
# of the substituted values are attacker-controlled shell metacharacters
# in this fleet's usage (SSH keys, IPs, hostnames) — but the password is
# opaque random output from openssl, so avoid sed/eval entirely for it.
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

cp "$TEMPLATE" "$TMP"
python3 - "$TMP" "$HOSTNAME_VAL" "$FQDN_DOMAIN" "$MGMT_CIDR" "$DISK_FILTER" "$SSH_PUBKEY" "$ROOT_PASSWORD" <<'PYEOF'
import sys

path, hostname, fqdn_domain, mgmt_cidr, disk_filter, ssh_pubkey, root_password = sys.argv[1:8]

with open(path) as f:
    content = f.read()

replacements = {
    "{{ HOSTNAME }}": hostname,
    "{{ FQDN_DOMAIN }}": fqdn_domain,
    "{{ MGMT_CIDR }}": mgmt_cidr,
    "{{ DISK_FILTER }}": disk_filter,
    "{{ SSH_PUBKEY }}": ssh_pubkey,
    "{{ ROOT_PASSWORD }}": root_password,
}
for placeholder, value in replacements.items():
    content = content.replace(placeholder, value)

with open(path, "w") as f:
    f.write(content)
PYEOF

mv "$TMP" "$OUT_FILE"
chmod 600 "$OUT_FILE"
trap - EXIT

echo "Rendered answer file written to: $OUT_FILE (mode 600, gitignored pattern — do not commit)" >&2

# Render the first-boot hook too — it only needs the pubkey substituted,
# but goes through the same template mechanism for consistency.
HOOK_TEMPLATE="${SCRIPT_DIR}/first-boot-hook.sh.tmpl"
HOOK_OUT="${OUT_FILE%.toml}.first-boot-hook.sh"
sed "s|{{ SSH_PUBKEY }}|${SSH_PUBKEY}|" "$HOOK_TEMPLATE" > "$HOOK_OUT"
chmod 700 "$HOOK_OUT"
echo "Rendered first-boot hook written to: $HOOK_OUT (mode 700, gitignored pattern — do not commit)" >&2

echo "Next: proxmox-auto-install-assistant validate-answer $OUT_FILE" >&2
echo "Then: proxmox-auto-install-assistant prepare-iso <source.iso> --fetch-from iso --answer-file $OUT_FILE --on-first-boot $HOOK_OUT --output <dest.iso>" >&2
