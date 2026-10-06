#!/usr/bin/env bash
# Pull each fleet host's /opt/homelab into /opt/homelab/backup-staging/<host>/
# so Backrest (docker-prod-01) can back up non-git host config. Runs on
# docker-prod-01 as kazuki via pull-staging.service (see systemd/).
#
# Source side is read-only: the key is restricted with
#   command="/usr/bin/rrsync -ro /opt/homelab",restrict,from="192.168.50.105"
# Files root-owned on a source host are skipped (rsync exit 23) and logged.
# --delete is deliberately NOT used: a path that becomes unreadable would
# otherwise be removed from staging, and the next snapshot would lose it.
set -uo pipefail

STAGING=/opt/homelab/backup-staging
KEY="$HOME/.ssh/homelab_backup_pull"
KNOWN_HOSTS="$HOME/.ssh/known_hosts"

# name ip
HOSTS=(
  "proxy-prod-01 192.168.50.107"
  "telemetry-prod-01 192.168.50.106"
  "core-01 192.168.50.3"
  "forgejo-prod-01 192.168.50.108"
  "garage-prod-01 192.168.50.80"
  "docker-prod-02 192.168.50.100"
)

# Heartbeat to Uptime Kuma (core-01). Push URLs live in kuma.env, not in
# this repo. Read with grep: the URLs contain '&', which `source` would break.
kuma_ping() { # $1 = variable name, $2 = up|down, $3 = message word
  local url
  url=$(grep -m1 "^$1=" "$HOME/homelab-backup/kuma.env" 2>/dev/null | cut -d= -f2-)
  [ -n "$url" ] || return 0
  # Rebuild the query from the base URL. A pattern-substitution replacement
  # treats '&' as "matched text" in bash 5.2+, which mangles the query.
  url="${url%%\?*}?status=$2&msg=$3&ping="
  curl -fsS -m 20 -o /dev/null "$url" || echo "kuma push failed ($1)"
}

failed=0
for entry in "${HOSTS[@]}"; do
  read -r name ip <<<"$entry"
  dest="$STAGING/$name"
  mkdir -p "$dest"

  # Crowdsec API credentials are excluded: they are live secrets, not config.
  rsync -a --partial --timeout=120 \
    --exclude='gateway/crowdsec/config/*_credentials.yaml' \
    -e "ssh -i $KEY -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$KNOWN_HOSTS" \
    "kazuki@$ip:" "$dest/"
  rc=$?

  count=$(find "$dest" -type f | wc -l)
  if [ "$count" -eq 0 ]; then
    echo "$name: FAILED — staging empty (rsync exit $rc)"
    failed=1
  elif [ "$rc" -eq 0 ]; then
    echo "$name: ok ($count files)"
  elif [ "$rc" -eq 23 ]; then
    echo "$name: partial — root-owned paths skipped (exit 23, $count files staged)"
  else
    echo "$name: FAILED (rsync exit $rc, $count files present from earlier runs)"
    failed=1
  fi
done

if [ "$failed" -eq 0 ]; then
  kuma_ping KUMA_PUSH_PULL_STAGING up ok
else
  kuma_ping KUMA_PUSH_PULL_STAGING down failed
fi

exit "$failed"
