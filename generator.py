#!/usr/bin/env python3
"""
generator.py — Generate GitHub Pages HTML from filtered papers.

Reads filtered paper JSON from stdin.
Generates:
- index.html (latest papers)
- archive/YYYY-MM-DD.html (daily archives)
- archive/index.html (list of archive dates)

Usage: python3 generator.py < filtered.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

# China timezone
CHINA_TZ = timezone(timedelta(hours=8))

# Blog theme (matching https://blog.isshikih.top/)
BG_COLOR = "#ffffff"
CARD_COLOR = "#ffffff"
ACCENT_COLOR = "#a27b5c"
TEXT_COLOR = "#383838"
MUTED_COLOR = "#666666"
LIGHTER_COLOR = "#999999"
BORDER_COLOR = "#f0f0f0"
LINK_COLOR = "#383838"
LINK_HOVER = "#876a53"
BOLD_COLOR = "#81a263"
FONT_FAMILY = "optima, Philosopher, Helvetica, Arial, Verdana, sans-serif"


def get_today_str() -> str:
    """Get today's date in China time as YYYY-MM-DD."""
    return datetime.now(CHINA_TZ).strftime("%Y-%m-%d")


def get_today_display() -> str:
    """Get a human-readable date string in Chinese."""
    now = datetime.now(CHINA_TZ)
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    return now.strftime(f"%Y 年 %m 月 %d 日 星期{weekdays[now.weekday()]}")


def extract_project_url(entry: dict) -> str | None:
    return entry.get("project_page_url") or None


def render_bold(text: str) -> str:
    """Convert **bold** markdown to <strong class="kw"> for HTML rendering (sage green)."""
    return re.sub(r'\*\*(.+?)\*\*', r'<strong class="kw">\1</strong>', text)


def generate_html(today_str: str, today_display: str, papers: list[dict]) -> str:
    """Generate the main HTML page."""
    cards_html = []
    for i, paper in enumerate(papers, 1):
        summary = paper.get("chinese_summary", {})
        task = summary.get("task_setting", "")
        motivation = summary.get("motivation", "")
        solution = summary.get("solution", "")

        proj_url = extract_project_url(paper)

        links_html = f"""
            <div class="paper-links">
                <a href="{paper['arxiv_url']}" class="link-btn" target="_blank">arXiv</a>
                <a href="{paper['pdf_url']}" class="link-btn" target="_blank">PDF</a>"""

        if proj_url:
            links_html += f'\n                <a href="{proj_url}" class="link-btn project" target="_blank">Project Page</a>'

        links_html += "\n            </div>"

        card = f"""
        <div class="paper-card">
            <h2 class="paper-title">
                <a href="{paper['arxiv_url']}" target="_blank">{paper['title']}</a>
            </h2>
            <div class="paper-authors">{paper.get('authors', '')}</div>
            <div class="paper-summary">
                <div class="summary-row">
                    <span class="summary-label">任务设定</span>
                    <span class="summary-text">{render_bold(task)}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">痛点动机</span>
                    <span class="summary-text">{render_bold(motivation)}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">解决方案</span>
                    <span class="summary-text">{render_bold(solution)}</span>
                </div>
            </div>
            {links_html}
        </div>"""
        cards_html.append(card)

    papers_content = "\n".join(cards_html)

    if not papers:
        papers_content = """
        <div class="empty-state">
            <p>📭 今天没有找到相关论文</p>
            <p class="hint">arXiv 在周五和周六不公布新文章，周末的投稿会在周日/周一一并公布。</p>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Paper Feed — {today_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {BG_COLOR};
            color: {TEXT_COLOR};
            font-family: {FONT_FAMILY};
            line-height: 1.6;
            min-height: 100vh;
        }}
        ::selection {{
            background: {BORDER_COLOR};
        }}
        a {{
            color: {LINK_COLOR};
            text-decoration: none;
            transition: color 0.2s;
        }}
        a:hover {{
            color: {LINK_HOVER};
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        header {{
            margin-bottom: 40px;
            text-align: center;
        }}
        header h1 {{
            font-size: 1.6rem;
            color: {ACCENT_COLOR};
            margin-bottom: 8px;
            font-weight: 400;
        }}
        header .subtitle {{
            font-size: 0.9rem;
            color: {MUTED_COLOR};
        }}
        header .subtitle a {{
            color: {LINK_COLOR};
        }}
        header .subtitle a:hover {{
            color: {LINK_HOVER};
        }}
        .paper-card {{
            background: {CARD_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 24px 28px;
            margin-bottom: 20px;
            border-bottom: 1px solid {BORDER_COLOR};
            position: relative;
        }}
        .paper-card:last-child {{
            border-bottom: none;
        }}
        .paper-card:hover {{
            border-color: {ACCENT_COLOR};
        }}
        .paper-title {{
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 14px;
            line-height: 1.4;
        }}
        .paper-title a {{
            color: {TEXT_COLOR};
        }}
        .paper-title a:hover {{
            color: {LINK_HOVER};
        }}
        .paper-authors {{
            font-size: 0.82rem;
            color: {MUTED_COLOR};
            margin-bottom: 14px;
            line-height: 1.4;
        }}
        .paper-summary {{
            margin-bottom: 14px;
        }}
        .summary-row {{
            margin-bottom: 6px;
            display: flex;
            gap: 8px;
        }}
        .summary-label {{
            flex-shrink: 0;
            font-size: 0.78rem;
            font-weight: 600;
            color: {ACCENT_COLOR};
            padding: 1px 6px;
            min-width: 56px;
        }}
        .summary-text {{
            font-size: 0.88rem;
            color: {TEXT_COLOR};
            line-height: 1.5;
        }}
        .summary-text strong.kw {{
            color: {BOLD_COLOR};
            font-weight: 600;
        }}
        .paper-links {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .link-btn {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.82rem;
            color: {LINK_COLOR};
            border: 1px solid {BORDER_COLOR};
            transition: all 0.2s;
        }}
        .link-btn:hover {{
            color: {LINK_HOVER};
            border-color: {LINK_COLOR};
        }}
        .link-btn.project {{
            color: {MUTED_COLOR};
            border-color: {BORDER_COLOR};
        }}
        .link-btn.project:hover {{
            color: {LINK_HOVER};
            border-color: {LINK_COLOR};
        }}
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
        }}
        .empty-state p {{
            font-size: 1.1rem;
            margin-bottom: 12px;
        }}
        .empty-state .hint {{
            font-size: 0.85rem;
            color: {LIGHTER_COLOR};
        }}
        footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 20px;
            font-size: 0.78rem;
            color: {LIGHTER_COLOR};
            border-top: 1px solid {BORDER_COLOR};
        }}
        @media (max-width: 600px) {{
            .container {{ padding: 24px 16px; }}
            header h1 {{ font-size: 1.3rem; }}
            .paper-card {{ padding: 18px 20px; }}
            .paper-title {{ font-size: 0.95rem; }}
            .summary-row {{ flex-direction: column; gap: 2px; }}
            .summary-label {{ align-self: flex-start; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Daily Paper Feed</h1>
            <div class="subtitle">
                {today_display} · 共 {len(papers)} 篇相关论文 ·
                <a href="archive/">历史存档</a>
            </div>
        </header>

        {papers_content}

        <footer>
            <p>Daily Paper Feed · 自动筛选自 arXiv</p>
        </footer>
    </div>
</body>
</html>"""
    return html


def generate_archive_index(archives: list[str]) -> str:
    """Generate the archive index page listing all available dates."""
    items_html = []
    for date_str in sorted(archives, reverse=True):
        items_html.append(
            f'        <li><a href="{date_str}.html">{date_str}</a></li>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Paper Feed — 历史存档</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {BG_COLOR};
            color: {TEXT_COLOR};
            font-family: {FONT_FAMILY};
            line-height: 1.6;
            min-height: 100vh;
        }}
        ::selection {{
            background: {BORDER_COLOR};
        }}
        a {{
            color: {LINK_COLOR};
            text-decoration: none;
        }}
        a:hover {{
            color: {LINK_HOVER};
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        h1 {{
            font-size: 1.4rem;
            font-weight: 400;
            color: {ACCENT_COLOR};
            margin-bottom: 8px;
        }}
        .back {{
            margin-bottom: 30px;
        }}
        .back a {{
            color: {LINK_COLOR};
            font-size: 0.9rem;
        }}
        ul {{
            list-style: none;
        }}
        li {{
            margin-bottom: 8px;
        }}
        li a {{
            color: {TEXT_COLOR};
            font-size: 0.95rem;
            padding: 8px 16px;
            display: block;
            border: 1px solid {BORDER_COLOR};
            border-radius: 6px;
            transition: all 0.2s;
        }}
        li a:hover {{
            border-color: {LINK_COLOR};
            color: {LINK_HOVER};
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="back"><a href="../">← 返回最新</a></div>
        <h1>历史存档</h1>
        <p style="color: {LIGHTER_COLOR}; margin-bottom: 24px;">共 {len(archives)} 期</p>
        <ul>
            {''.join(items_html)}
        </ul>
    </div>
</body>
</html>"""


def main():
    papers = json.load(sys.stdin)
    # Use today's date (China time) for the page
    today_str = get_today_str()
    today_display = get_today_display()

    print(f"Generating page for {today_str} with {len(papers)} papers", file=sys.stderr)

    repo_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate index.html
    index_html = generate_html(today_str, today_display, papers)
    index_path = os.path.join(repo_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  → index.html", file=sys.stderr)

    # Generate archive page
    archive_dir = os.path.join(repo_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)

    archive_path = os.path.join(archive_dir, f"{today_str}.html")
    archive_html = generate_html(today_str, today_display, papers)
    # Fix archive page nav to point back properly
    archive_html = archive_html.replace(
        '<a href="archive/">历史存档</a>',
        '<a href="index.html">全部存档</a>'
    )
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(archive_html)
    print(f"  → archive/{today_str}.html", file=sys.stderr)

    # Generate/update archive/index.html
    existing_archives = []
    if os.path.exists(archive_dir):
        for fname in sorted(os.listdir(archive_dir)):
            if fname.endswith(".html") and fname != "index.html":
                existing_archives.append(fname.replace(".html", ""))

    if today_str not in existing_archives:
        existing_archives.append(today_str)

    archive_index_html = generate_archive_index(existing_archives)
    archive_index_path = os.path.join(archive_dir, "index.html")
    with open(archive_index_path, "w", encoding="utf-8") as f:
        f.write(archive_index_html)
    print(f"  → archive/index.html ({len(existing_archives)} archives)", file=sys.stderr)

    print(f"\nPages generated at:", file=sys.stderr)
    print(f"  file://{index_path}", file=sys.stderr)
    print(f"  file://{archive_path}", file=sys.stderr)


if __name__ == "__main__":
    main()