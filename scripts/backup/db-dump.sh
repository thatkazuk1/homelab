#!/usr/bin/env bash
# Logical dumps of this host's Postgres containers into /opt/homelab/db-dumps/<stack>/.
# Credentials stay inside each container (POSTGRES_USER/DB read by the shell
# inside the container); nothing secret is printed or stored on the host.
#
# Usage: db-dump.sh <manifest>
# Manifest lines: stack|container|engine|keep_days|keep_monthly_months
#   engine: postgres (only engine supported in phase 1)
#   keep_monthly_months: 0 = none; N = keep the 1st-of-month dump for N months
#
# Output is pulled to docker-prod-01 by pull-staging.sh (every host's /opt/homelab).
set -uo pipefail

OUT=/opt/homelab/db-dumps
MANIFEST=${1:?usage: db-dump.sh <manifest>}
failed=0

while IFS='|' read -r stack container engine keep_days keep_months; do
  [[ -z "$stack" || "$stack" == \#* ]] && continue
  dir="$OUT/$stack"
  mkdir -p "$dir"
  ts=$(date +%Y-%m-%d_%H%M)

  case "$engine" in
    postgres)
      final="$dir/$ts.dump"
      tmp="$final.partial"
      # pg_dump runs inside the container, so the password never leaves it.
      if ! docker exec "$container" sh -c 'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$tmp"; then
        echo "$stack: FAILED — pg_dump exited non-zero ($container)"
        rm -f "$tmp"; failed=1; continue
      fi
      # Validate the archive table of contents (metadata only).
      if ! docker exec -i "$container" pg_restore --list < "$tmp" > /dev/null 2>&1; then
        echo "$stack: FAILED — dump failed pg_restore --list validation"
        rm -f "$tmp"; failed=1; continue
      fi
      if [ ! -s "$tmp" ]; then
        echo "$stack: FAILED — empty dump"; rm -f "$tmp"; failed=1; continue
      fi
      mv "$tmp" "$final"
      echo "$stack: ok ($(du -h "$final" | cut -f1))"
      ;;
    *)
      echo "$stack: FAILED — unsupported engine '$engine'"; failed=1; continue ;;
  esac

  # Retention: drop dumps older than keep_days, except 1st-of-month dumps
  # within keep_months. Filenames start with YYYY-MM-DD, so string compare is date compare.
  cutoff_daily=$(date -d "-${keep_days} days" +%F)
  cutoff_monthly=$(date -d "-$((keep_months * 31)) days" +%F)
  for f in "$dir"/*.dump; do
    [ -e "$f" ] || continue
    d=$(basename "$f" | cut -c1-10)
    if [[ "$d" < "$cutoff_daily" ]]; then
      if [ "${d:8:2}" = "01" ] && [ "$keep_months" -gt 0 ] && [[ "$d" > "$cutoff_monthly" ]]; then
        continue
      fi
      rm -f "$f"
    fi
  done
done < "$MANIFEST"

# Heartbeat to Uptime Kuma. Push URL lives in kuma.env; read with grep, not
# source, because the URL contains '&'.
kuma_ping() { # $1 = up|down, $2 = message word
  local url
  url=$(grep -m1 '^KUMA_PUSH_DB_DUMP=' "$HOME/homelab-backup/kuma.env" 2>/dev/null | cut -d= -f2-)
  [ -n "$url" ] || return 0
  # Rebuild the query from the base URL. A pattern-substitution replacement
  # treats '&' as "matched text" in bash 5.2+, which mangles the query.
  url="${url%%\?*}?status=$1&msg=$2&ping="
  curl -fsS -m 20 -o /dev/null "$url" || echo "kuma push failed"
}
if [ "$failed" -eq 0 ]; then kuma_ping up ok; else kuma_ping down failed; fi

exit "$failed"
