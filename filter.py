#!/usr/bin/env python3
"""
filter.py — Filter papers for relevance and write Chinese summaries.

Reads paper JSON from stdin, batches them, and uses Claude CLI to:
1. Judge relevance based on user's research interests
2. Write Chinese summaries for relevant papers

Usage: python3 filter.py < papers.json > filtered.json
"""

import json
import os
import subprocess
import sys

# Config file path (local, not committed to git)
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paperfeed_config.json")


def load_research_interests() -> str:
    """Load research interests from config file."""
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        interests = config.get("research_interests", [])
        if not interests:
            print("Warning: No research_interests found in config", file=sys.stderr)
            return ""
        return "\n".join(f"- {interest}" for interest in interests)
    except FileNotFoundError:
        print(f"Error: Config file not found at {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid config JSON: {e}", file=sys.stderr)
        sys.exit(1)

BATCH_SIZE = 20
CLAUDE_CMD = ["claude", "-p", "--print", "--dangerously-skip-permissions", "--model", "claude-sonnet-5"]


def build_batch_prompt(batch: list[dict], batch_num: int, total_batches: int) -> str:
    """Build a prompt for Claude to analyze a batch of papers."""
    research_interests = load_research_interests()
    papers_text = []
    for i, paper in enumerate(batch):
        papers_text.append(f"""=== PAPER {i + 1} ===
arxiv_id: {paper['arxiv_id']}
title: {paper['title']}
category: {paper.get('category', 'unknown')}
abstract: {paper['abstract'][:1500]}
""")

    papers_str = "\n".join(papers_text)

    prompt = f"""You are analyzing batch {batch_num}/{total_batches} of newly announced arXiv papers.

For each paper, determine if it's relevant to the user's research interests (below), and if so, write a concise Chinese summary.

RESEARCH INTERESTS:
{research_interests}

For each paper, decide: IS_YES_RELEVANT or IS_NOT_RELEVANT.

If relevant, provide:
1. task_setting: What problem/task does this paper address? (1 short sentence in Chinese, < 40 chars)
2. motivation: Why is this hard or what pain point does it solve? (1 short sentence in Chinese, < 40 chars)
3. solution: What approach does it propose? Use plain, easy-to-understand Chinese. (1-2 sentences, < 60 chars total)
4. project_page_url: Extract from the abstract any project page URL (like https://*.github.io or https://*.com), or null if none found.

**Bolding rule:** In each of the three Chinese summary fields, wrap **1-2 key technical terms** in `**` for emphasis. This helps ADHD readers scan quickly. Keep bolding sparse — only the most important concept per field. Example: "利用**预训练视频模型**的运动先验，通过**轻量适配器**转成3D场景流预测"

OUTPUT FORMAT: ONLY output a valid JSON array. No other text. Each element is:
{{
  "arxiv_id": "the arxiv id",
  "is_relevant": true,
  "chinese_summary": {{
    "task_setting": "...",
    "motivation": "...",
    "solution": "..."
  }},
  "project_page_url": "https://..." or null
}}

For irrelevant papers:
{{
  "arxiv_id": "the arxiv id",
  "is_relevant": false
}}

IMPORTANT: Return EXACTLY {len(batch)} items in the array, one per paper, in the same order.

Papers to analyze:
{papers_str}"""

    return prompt


def call_claude(prompt: str) -> str:
    """Call Claude CLI and return stdout."""
    try:
        result = subprocess.run(
            CLAUDE_CMD,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"Claude CLI error (exit {result.returncode}): {result.stderr[:500]}", file=sys.stderr)
            return ""
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("Claude CLI timed out after 120s", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("Claude CLI not found. Is it installed?", file=sys.stderr)
        sys.exit(1)


def parse_claude_output(stdout: str) -> list[dict]:
    """Parse Claude's JSON output, trying to extract a valid JSON array."""
    if not stdout:
        return []

    # Try direct JSON parse
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array between ``` markers
    import re
    m = re.search(r'```(?:json)?\s*\n?(\[[\s\S]*?\])\n?\s*```', stdout)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON array in the output
    m = re.search(r'(\[[\s\S]*?\])', stdout)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    print(f"Failed to parse Claude output as JSON. Output length: {len(stdout)}", file=sys.stderr)
    print(f"First 500 chars: {stdout[:500]}", file=sys.stderr)
    return []


def main():
    papers = json.load(sys.stdin)

    # Deduplicate by arxiv_id (same paper may appear in multiple categories)
    seen_ids = set()
    deduped = []
    for p in papers:
        aid = p["arxiv_id"]
        if aid not in seen_ids:
            seen_ids.add(aid)
            deduped.append(p)
    papers = deduped
    print(f"Deduplicated input: {len(papers)} unique papers", file=sys.stderr)
    total = len(papers)
    print(f"Filtering {total} papers in batches of {BATCH_SIZE}...", file=sys.stderr)

    batches = [papers[i:i + BATCH_SIZE] for i in range(0, len(papers), BATCH_SIZE)]
    total_batches = len(batches)

    all_results = []
    total_relevant = 0

    for batch_num, batch in enumerate(batches, 1):
        print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} papers)...", file=sys.stderr)
        prompt = build_batch_prompt(batch, batch_num, total_batches)
        stdout = call_claude(prompt)

        if not stdout:
            print(f"  Warning: Empty response for batch {batch_num}", file=sys.stderr)
            continue

        results = parse_claude_output(stdout)
        if not results:
            print(f"  Warning: Could not parse results for batch {batch_num}", file=sys.stderr)
            continue

        if len(results) != len(batch):
            print(f"  Warning: Expected {len(batch)} results, got {len(results)}", file=sys.stderr)

        # Build lookup from results
        result_map = {}
        for r in results:
            result_map[r["arxiv_id"]] = r

        # Match results back to papers
        for paper in batch:
            arxiv_id = paper["arxiv_id"]
            result = result_map.get(arxiv_id)
            if not result:
                continue

            if result.get("is_relevant"):
                # Build output entry
                summary = result.get("chinese_summary", {})
                entry = {
                    "arxiv_id": arxiv_id,
                    "title": paper["title"],
                    "authors": paper.get("authors", ""),
                    "category": paper.get("category", ""),
                    "arxiv_url": paper["arxiv_url"],
                    "pdf_url": paper["pdf_url"],
                    "project_page_url": result.get("project_page_url"),
                    "chinese_summary": {
                        "task_setting": summary.get("task_setting", ""),
                        "motivation": summary.get("motivation", ""),
                        "solution": summary.get("solution", ""),
                    },
                }
                all_results.append(entry)
                total_relevant += 1

        print(f"  Relevant so far: {total_relevant}/{len(all_results)}", file=sys.stderr)

    print(f"\nDone. {total_relevant} relevant papers found out of {total} total.", file=sys.stderr)

    # Output filtered papers
    json.dump(all_results, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()