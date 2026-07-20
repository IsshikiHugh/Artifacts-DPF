You are building a Daily Paper Feed GitHub Pages site in /home/ut/agent/agent_workspace/Artifacts-DailyPaperFeed. The repo is empty except for README.md.

## SPECIFICATION

### Purpose
A static GitHub Pages site that lists freshly announced arXiv papers from cs.CV and cs.AI categories, filtered for relevance to the user's research interests. Each paper gets a Chinese summary.

### Data source
- https://papers.cool/arxiv/cs.CV — Computer Vision papers
- https://papers.cool/arxiv/cs.AI — AI papers
- These mirror arXiv's announcement schedule. Papers are announced Sunday through Thursday (20:00 ET), no updates Friday-Saturday.

### User research interests (filter criteria)
- Human motion / pose estimation / mesh recovery (SMPL, human mesh)
- Human-scene interaction / 3D scene understanding
- Video generation / video diffusion models
- Embodied AI / robot learning / policy learning
- 3D human reconstruction / 4D human / human digitization
- Egocentric vision / hand-object interaction
- MLLM (multimodal LLM) reasoning / visual grounding
- AI agents / tool-use / planning / reasoning
- Video understanding / long video QA / spatio-temporal reasoning
- Image/video generation and editing

### Architecture (three Python scripts + one shell runner)

#### 1. scraper.py
- Takes a date argument (YYYY-MM-DD format, defaults to today's date)
- Fetches the HTML from https://papers.cool/arxiv/cs.CV and https://papers.cool/arxiv/cs.AI
- The page shows papers for a specific date (the announcement date, shown in the .date element)
- Parses each paper entry: arxiv id, title, authors, abstract, subjects, publish date, PDF link, all related links
- Since papers.cool pages display ALL papers for one day, we extract the "Total: N" count and all paper divs
- Each paper div has id="ARXIVID" and contains: h2.title, #authors-, #summary-, #subjects-, #date- elements
- Returns JSON output to stdout: list of paper dicts with keys: arxiv_id, title, authors, abstract, subjects, publish_date, arxiv_url, pdf_url
- IMPORTANT: papers.cool shows the date in the page (e.g. "2026-07-20"). If the page shows a different date than requested, it means the site hasn't updated yet for that date. Check the .date element's text content to get the actual date being displayed.
- Handle HTTP errors gracefully - exit with error message if fetch fails
- DO NOT call any LLM/AI. This is pure data extraction.

#### 2. filter.py
- Reads paper JSON from stdin (pipe from scraper.py output or a JSON file)
- Filters papers for relevance using an LLM call
- For each paper, calls the LLM to determine:
  1. Is this paper relevant to the user's research interests? (yes/no)
  2. If yes, write a Chinese summary (3 sentences max, in this format):
     - Task setting: what problem/task does this paper address
     - Motivation: why is this hard or what pain point does it solve
     - Solution: what approach does it propose, in plain simple Chinese
  3. If the paper has a project page URL (found in the abstract text), extract it
- Strategy: batch papers (up to 20 at a time) to reduce LLM calls
- Output JSON: list of filtered papers with fields: arxiv_id, title, chinese_summary (dict with task_setting, motivation, solution), arxiv_url, project_page_url (or null), pdf_url
- Use subprocess to call: claude -p --print --dangerously-skip-permissions --model 'anthropic/claude-opus-4-5-xhigh'
- The prompt to Claude should ask it to analyze papers and return structured JSON
- If a paper is not relevant, exclude it from output

#### 3. generator.py
- Reads filtered paper JSON from stdin
- Generates index.html — a clean, modern GitHub Pages compatible HTML page
- The page should:
  - Have a dark theme (the user likes dark/black/purple aesthetic)
  - Show the date prominently
  - List each paper as a card with:
    - Title (linked to arXiv)
    - Chinese summary (Task → Motivation → Solution in nice formatting)
    - Links row: arXiv, PDF, Project Page (if available)
  - Be responsive and clean. Pure HTML+CSS, no external dependencies
  - Self-contained single file (no JS frameworks)
  - Archive link in header
- Also generates archive/YYYY-MM-DD.html with the same content for historical records
- Creates an archive/index.html that lists all available dates

#### 4. run.sh (entry point)
```bash
#!/bin/bash
# Run the daily paper feed pipeline
# Usage: ./run.sh [date]
set -euo pipefail
DATE="${1:-$(date +%Y-%m-%d)}"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"
echo "=== Daily Paper Feed: $DATE ==="
python3 scraper.py "$DATE" > /tmp/paperfeed_raw_$DATE.json
python3 filter.py < /tmp/paperfeed_raw_$DATE.json > /tmp/paperfeed_filtered_$DATE.json
python3 generator.py < /tmp/paperfeed_filtered_$DATE.json
git add -A
git commit -m "daily paper feed: $DATE"
git push origin main
```

### IMPORTANT IMPLEMENTATION NOTES

1. For scraper.py: Parse the papers.cool HTML properly. Each paper is in a div with class "panel paper" and id="ARXIV_ID". The page structure is:
   ```
   <div id="2607.16193" class="panel paper" keywords="...">
     <h2 class="title">
       <a href="https://arxiv.org/abs/2607.16193" ...>Title text</a>
     </h2>
     <p id="authors-2607.16193" class="metainfo authors">Authors: ...</p>
     <p id="summary-2607.16193" class="summary">Abstract text...</p>
     <p id="subjects-2607.16193" class="metainfo subjects">Subject: ...</p>
     <p id="date-2607.16193" class="metainfo date">Publish: 2026-07-17 17:59:56 UTC</p>
   </div>
   ```
   Use regex to parse (no BeautifulSoup dependency).

2. For filter.py: The LLM call is the bottleneck. Use a smart batching approach. Design the Claude prompt to return clean JSON. Use subprocess.run with capture_output=True.

3. For the generator HTML: Use a clean dark theme. Colors: background #0d0d1a, cards #1a1a2e, accent #7c5cbf (purple), text #e0e0e0. Single file, responsive, no external dependencies.

4. The summary field should be a dict with task_setting, motivation, solution as separate strings.

Write ALL files. Make sure the code actually works — test scraper.py on the actual papers.cool site before finishing. Do not skip testing.