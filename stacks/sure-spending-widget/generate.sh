#!/bin/sh
set -eu

SURE_URL="${SURE_URL:-https://sure.ts.kazuki.uk}"
OUT="/output/sure-spending.json"
TMP="/output/.sure-spending.json.tmp"

# Calendar week (Monday start, matching Sure's own dashboard - Rails'
# ActiveSupport default beginning_of_week is Monday and this app doesn't
# override it) and calendar month-to-date, both matching Sure's dashboard
# definition of "current_week"/"current_month" in app/models/period.rb.
today_epoch=$(date +%s)
dow=$(date +%u) # 1=Monday .. 7=Sunday
week_start_epoch=$(( today_epoch - (dow - 1) * 86400 ))

today=$(date +%Y-%m-%d)
week_start=$(date -d "@${week_start_epoch}" +%Y-%m-%d)
month_start=$(date +%Y-%m-01)

# Calls Sure's MCP get_income_statement tool, which drives the same
# family.income_statement.expense_totals/income_totals(period:) queries as
# Sure's own dashboard cash-flow widget (app/controllers/pages_controller.rb)
# - confirmed by reading app/models/income_statement.rb at the currently
# running tag. Prints the raw JSON-RPC response on stdout; callers pull
# whichever of .expense.total / .income.total they need via jq, so one call
# covers both instead of fetching the same period twice.
fetch_income_statement() {
  start_date="$1"
  end_date="$2"

  curl -sf -X POST "${SURE_URL}/mcp" \
    -H "Authorization: Bearer ${MCP_API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"get_income_statement\",\"arguments\":{\"start_date\":\"${start_date}\",\"end_date\":\"${end_date}\"}}}" \
    | jq -er '.result.content[0].text | fromjson'
}

week_stmt=$(fetch_income_statement "${week_start}" "${today}") || { echo "generate.sh: failed to fetch week statement" >&2; exit 1; }
month_stmt=$(fetch_income_statement "${month_start}" "${today}") || { echo "generate.sh: failed to fetch month statement" >&2; exit 1; }

week_total=$(echo "${week_stmt}" | jq -er '.expense.total')
month_total=$(echo "${month_stmt}" | jq -er '.expense.total')
month_income_total=$(echo "${month_stmt}" | jq -er '.income.total')

jq -n \
  --arg week_total "${week_total}" \
  --arg month_total "${month_total}" \
  --arg month_income_total "${month_income_total}" \
  --arg week_start "${week_start}" \
  --arg month_start "${month_start}" \
  --arg today "${today}" \
  --arg updated_at "$(date -Iseconds)" \
  '{
    week: { total: $week_total, start_date: $week_start, end_date: $today },
    month: { total: $month_total, income_total: $month_income_total, start_date: $month_start, end_date: $today },
    updated_at: $updated_at
  }' > "${TMP}"

mv "${TMP}" "${OUT}"
echo "generate.sh: wrote ${OUT} (week=${week_total} month=${month_total} month_income=${month_income_total})"
