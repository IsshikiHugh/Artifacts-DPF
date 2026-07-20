#!/bin/bash
# Daily Paper Feed pipeline
# Usage: ./run.sh [YYYY-MM-DD]
# If date is omitted, uses the latest date available on papers.cool.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "============================================"
echo "  Daily Paper Feed"
echo "============================================"

# Step 1: Scrape papers from papers.cool
echo ""
echo "[1/3] Scraping papers from papers.cool..."

# Run scraper without date to get the latest available page
# Capture stderr separately to extract the page date
python3 scraper.py "$@" > /tmp/paperfeed_raw_latest.json 2>/tmp/paperfeed_raw_stderr.txt
cat /tmp/paperfeed_raw_stderr.txt

# Extract the actual date from stderr (the page date shown by papers.cool)
PAGE_DATE=$(grep -oP 'page date: \K\d{4}-\d{2}-\d{2}' /tmp/paperfeed_raw_stderr.txt | head -1)
DATE="${1:-$PAGE_DATE}"

if [ -z "$DATE" ]; then
    # Fallback to today's date if we can't extract it
    DATE="$(date +%Y-%m-%d)"
fi

RAW_COUNT=$(python3 -c "import json; d=json.load(open('/tmp/paperfeed_raw_latest.json')); print(len(d))")
echo "  → $RAW_COUNT papers fetched (date: $DATE)"

# If no papers, still generate the page (shows empty state) and commit
if [ "$RAW_COUNT" -eq 0 ]; then
    echo "  No papers found. Generating empty page..."
    echo '[]' | python3 generator.py
    git add -A
    git commit -m "daily paper feed: $DATE (no papers)" || true
    git push origin main
    echo ""
    echo "============================================"
    echo "  Done! No papers for $DATE"
    echo "============================================"
    exit 0
fi

# Step 2: Filter and summarize
echo ""
echo "[2/3] Filtering papers and writing Chinese summaries..."
python3 filter.py < /tmp/paperfeed_raw_latest.json > /tmp/paperfeed_filtered_latest.json
FILTERED_COUNT=$(python3 -c "import json; d=json.load(open('/tmp/paperfeed_filtered_latest.json')); print(len(d))")
echo "  → $FILTERED_COUNT relevant papers"

# Step 3: Generate HTML pages
echo ""
echo "[3/3] Generating GitHub Pages HTML..."
python3 generator.py < /tmp/paperfeed_filtered_latest.json

# Step 4: Commit and push
echo ""
echo "Committing and pushing to GitHub..."
git add -A
git commit -m "daily paper feed: $DATE"
git push origin main

echo ""
echo "============================================"
echo "  Done! $DATE paper feed published"
echo "============================================"