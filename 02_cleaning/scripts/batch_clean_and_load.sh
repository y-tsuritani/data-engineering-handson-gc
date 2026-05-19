#!/usr/bin/env bash
set -euo pipefail

FUNCTION_URL="https://asia-northeast1-${PROJECT_ID}.cloudfunctions.net/clean-and-load"

for csv in data/transactions/*.csv; do
  date=$(basename "${csv}" .csv | sed 's/transactions_//')
  echo "Processing ${date}..."
  curl -s -X POST "${FUNCTION_URL}" \
    -H "Content-Type: application/json" \
    -d "{\"date\": \"${date}\"}"
  echo ""
done
