#!/bin/bash
# Daily Paper Feed pipeline
# Usage: ./run.sh [YYYY-MM-DD]
# If date is omitted, uses today's date (China time).

set -euo pipefail

DATE="${1:-$(TZ='Asia/Shanghai' date +%Y-%m-%d)}"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "============================================"
echo "  Daily Paper Feed: $DATE"
echo "============================================"

# Step 1: Scrape papers from papers.cool
echo ""
echo "[1/3] Scraping papers from papers.cool..."
python3 scraper.py "$DATE" > /tmp/paperfeed_raw_"$DATE".json
RAW_COUNT=$(python3 -c "import json; d=json.load(open('/tmp/paperfeed_raw_$DATE.json')); print(len(d))")
echo "  → $RAW_COUNT papers fetched"

# Step 2: Filter and summarize
echo ""
echo "[2/3] Filtering papers and writing Chinese summaries..."
python3 filter.py < /tmp/paperfeed_raw_"$DATE".json > /tmp/paperfeed_filtered_"$DATE".json
FILTERED_COUNT=$(python3 -c "import json; d=json.load(open('/tmp/paperfeed_filtered_$DATE.json')); print(len(d))")
echo "  → $FILTERED_COUNT relevant papers"

# Step 3: Generate HTML pages
echo ""
echo "[3/3] Generating GitHub Pages HTML..."
python3 generator.py < /tmp/paperfeed_filtered_"$DATE".json

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