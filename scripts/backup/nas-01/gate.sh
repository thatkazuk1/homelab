#!/bin/sh
# Forced command for the backup pull key on nas-01 (see scripts/backup/pull-staging.sh).
# authorized_keys line, in /home/kazuki/.ssh/authorized_keys on nas-01:
#   command="/Volume1/@apps/backup/gate.sh",restrict,from="192.168.50.105" ssh-ed25519 <key> backup-pull@docker-prod-01
# The key can do exactly two things:
#   dump   make consistent copies of the live SQLite databases (dump.py)
#   rsync  read the app folder, read only (rrsync -ro)
# Anything else is refused. The account is UID 0 on TOS, so keep this file short.
ROOT=/Volume1/@apps/homelab
case "${SSH_ORIGINAL_COMMAND:-}" in
  dump)
    exec /usr/bin/python3 /Volume1/@apps/backup/dump.py
    ;;
  "rsync --server --sender "*)
    exec /usr/bin/rrsync -ro "$ROOT"
    ;;
  *)
    echo "gate.sh: command refused" >&2
    exit 1
    ;;
esac
