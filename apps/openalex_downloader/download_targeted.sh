#!/bin/bash
# Download AI safety papers from OpenAlex in targeted batches.
#
# Safe to re-run: each query gets its own subdirectory with its own checkpoint,
# so --resume correctly skips already-downloaded files within each query batch.
# Re-running after credit exhaustion will pick up exactly where each query left off.
#
# The CLI uses a single .openalex-checkpoint.json per output directory.
# If all queries shared one directory, --resume would abort on filter mismatch.
# Per-query subdirectories solve this: each has its own checkpoint + filter.
#
# import_openalex.py uses rglob("*.json") so it finds all files in all subdirs.

set -euo pipefail

FRESH=false
COUNT_ONLY=false
for arg in "$@"; do
  [[ "$arg" == "--fresh" ]] && FRESH=true
  [[ "$arg" == "--count-only" ]] && COUNT_ONLY=true
done

VENV="./venv/bin"
CLI="$VENV/openalex"
KEY="td1fSpoJ9COOKXpm4zXrPz"
BASE_OUT="./openalex_data"
WORKERS=8
SUBFIELD="primary_topic.subfield.id:1702,from_publication_date:2020-01-01"

QUERIES=(
  "RLHF
  "Constitutional AI"
  "mechanistic interpretability"
)

if $FRESH; then
  echo "--fresh: deleting all checkpoints..."
  find "$BASE_OUT" -name ".openalex-checkpoint.json" -delete
fi

for query in "${QUERIES[@]}"; do
  filter_query=$(echo "$query" | tr ' ' '+')
  full_filter="${SUBFIELD},default.search:${filter_query}"
  count=$(curl -s "https://api.openalex.org/works?filter=${full_filter}&per_page=1&api_key=${KEY}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['meta']['count'])" 2>/dev/null || echo "unknown")
  echo "$count  $query"

  if $COUNT_ONLY; then
    continue
  fi

  echo "========================================"
  echo "Downloading: $query"
  echo "========================================"

  subdir=$(echo "$query" | tr ' ' '_')
  query_out="$BASE_OUT/$subdir"
  mkdir -p "$query_out"

  # --resume: safe to re-run; skips already-downloaded work IDs for this query.
  # If credits run out mid-query, re-run tomorrow — it resumes from the cursor.
  $CLI download \
    --api-key "$KEY" \
    --output "$query_out" \
    --filter "${SUBFIELD},default.search:${filter_query}" \
    --nested \
    --workers "$WORKERS" \
    --resume \
  || {
    echo "Download stopped (likely credits exhausted). Re-run tomorrow to continue."
    break
  }
done

if $COUNT_ONLY; then
  exit 0
fi

echo ""
echo "All downloads complete!"
echo "Importing into SQLite (rglob finds all subdirectory files)..."
$VENV/python import_openalex.py "$BASE_OUT" openalex_local.db

echo "Done!"
