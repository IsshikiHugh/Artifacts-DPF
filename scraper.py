#!/usr/bin/env python3
"""
scraper.py — Fetch daily paper listings from papers.cool

Usage: python3 scraper.py [YYYY-MM-DD]
  If no date given, uses today's date.
  Outputs JSON array of paper dicts to stdout.

papers.cool uses infinite scroll with ?skip=N for pagination (25 papers per page).
"""

import json
import re
import sys
import urllib.request
import urllib.error

CATEGORIES = {
    "cs.CV": "https://papers.cool/arxiv/cs.CV",
    "cs.AI": "https://papers.cool/arxiv/cs.AI",
}
PAGE_SIZE = 25


def fetch_page(url: str) -> str:
    """Fetch HTML from papers.cool. Raises on HTTP error."""
    req = urllib.request.Request(url, headers={
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code} fetching {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL error fetching {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def extract_total(html: str) -> int:
    """Extract the total number of papers from the page."""
    m = re.search(r"Total:\s*(\d+)", html)
    if m:
        return int(m.group(1))
    return 0


def extract_page_date(html: str) -> str | None:
    """Extract the date shown on the papers.cool page."""
    m = re.search(
        r'openArxivCalendar\([^,]+,\s*[^,]+,\s*\'(\d{4}-\d{2}-\d{2})\'',
        html
    )
    if m:
        return m.group(1)
    return None


def parse_papers(html: str, category: str) -> list[dict]:
    """Parse all paper entries from one papers.cool HTML fragment.

    Handles both the initial page (full HTML) and paginated fragments (just paper divs).
    """
    papers = []

    # Each paper div has id="ARXIV_ID" and class="panel paper"
    pattern = r'<div\s+id="([^"]+)"\s+class="panel\s+paper"[^>]*>'
    splits = re.split(pattern, html)

    for i in range(1, len(splits) - 1, 2):
        arxiv_id = splits[i]
        content = splits[i + 1]
        # Truncate content at the closing </div> of the paper panel
        # to avoid bleeding into the next paper
        content = content.split("</div>")[0]

        paper = parse_single_paper(arxiv_id, content, category)
        if paper:
            papers.append(paper)

    return papers


def parse_single_paper(arxiv_id: str, content: str, category: str) -> dict | None:
    """Parse a single paper entry from its HTML content block."""
    # Title
    title_m = re.search(
        r'<a\s+id="title-' + re.escape(arxiv_id) + r'"[^>]*>([^<]+)</a>',
        content
    )
    if not title_m:
        return None
    title = title_m.group(1).strip()

    # Authors
    authors_m = re.search(
        r'<p\s+id="authors-' + re.escape(arxiv_id) + r'"[^>]*>.*?<strong>Authors?</strong>:\s*(.*?)</p>',
        content,
        re.DOTALL
    )
    authors = ""
    if authors_m:
        raw = authors_m.group(1)
        authors = re.sub(r'<[^>]+>', '', raw).strip()
        authors = re.sub(r'\s+', ' ', authors)

    # Abstract
    abstract_m = re.search(
        r'<p\s+id="summary-' + re.escape(arxiv_id) + r'"[^>]*class="summary[^"]*"[^>]*>(.*?)</p>',
        content,
        re.DOTALL
    )
    abstract = ""
    if abstract_m:
        raw = abstract_m.group(1)
        abstract = re.sub(r'<[^>]+>', '', raw).strip()
        abstract = re.sub(r'\s+', ' ', abstract)

    # Subjects
    subjects_m = re.search(
        r'<p\s+id="subjects-' + re.escape(arxiv_id) + r'"[^>]*>.*?<strong>Subjects?</strong>:\s*(.*?)</p>',
        content,
        re.DOTALL
    )
    subjects = []
    if subjects_m:
        raw = subjects_m.group(1)
        subject_links = re.findall(
            r'<a[^>]*href="/arxiv/([^"]+)"[^>]*>([^<]+)</a>',
            raw
        )
        subjects = [s[1] for s in subject_links]

    if not subjects:
        subjects_m2 = re.search(
            r'<p\s+id="subjects-' + re.escape(arxiv_id) + r'"[^>]*>.*?<strong>Subject</strong>:\s*(.*?)</p>',
            content,
            re.DOTALL
        )
        if subjects_m2:
            raw2 = subjects_m2.group(1)
            subject_links2 = re.findall(
                r'<a[^>]*href="/arxiv/([^"]+)"[^>]*>([^<]+)</a>',
                raw2
            )
            subjects = [s[1] for s in subject_links2]

    # Publish date
    date_m = re.search(
        r'<span[^>]*class="date-data"[^>]*>([^<]+)</span>',
        content,
    )
    publish_date = ""
    if date_m:
        publish_date = date_m.group(1).strip()

    # Build URLs
    arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "subjects": subjects,
        "publish_date": publish_date,
        "arxiv_url": arxiv_url,
        "pdf_url": pdf_url,
        "category": category,
    }


def fetch_all_papers_for_category(base_url: str, category: str, target_date: str) -> list[dict]:
    """Fetch ALL papers for a category, handling infinite scroll pagination."""
    # Build the initial URL
    if target_date:
        url = f"{base_url}?date={target_date}"
    else:
        url = base_url

    # Fetch first page
    html = fetch_page(url)
    page_date = extract_page_date(html)
    total = extract_total(html)

    if total == 0:
        print(f"  No papers found for {category} on this date", file=sys.stderr)
        return [], page_date or ""

    print(f"  {category}: {total} papers total (page date: {page_date or 'unknown'}), fetching with pagination...", file=sys.stderr)

    all_papers = []
    skip = 0

    while skip < total:
        if skip == 0:
            page_html = html
        else:
            page_url = f"{url}&skip={skip}" if "?" in url else f"{url}?skip={skip}"
            page_html = fetch_page(page_url)

        papers = parse_papers(page_html, category)
        all_papers.extend(papers)

        print(f"    skip={skip}: got {len(papers)} papers (total so far: {len(all_papers)})", file=sys.stderr)

        skip += PAGE_SIZE

    return all_papers


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    target_date = date_arg if date_arg else ""

    all_papers = []
    page_date = None

    for cat_name, cat_url in CATEGORIES.items():
        papers = fetch_all_papers_for_category(cat_url, cat_name, target_date)
        all_papers.extend(papers)

    # Sort by publish_date descending (newest first)
    all_papers.sort(key=lambda p: p["publish_date"], reverse=True)

    print(f"\nTotal papers fetched across all categories: {len(all_papers)}", file=sys.stderr)

    # Output JSON
    json.dump(all_papers, sys.stdout, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()