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
import sys
from datetime import datetime, timezone, timedelta

# China timezone
CHINA_TZ = timezone(timedelta(hours=8))

# Colors and theme
BG_COLOR = "#0d0d1a"
CARD_COLOR = "#1a1a2e"
ACCENT_COLOR = "#7c5cbf"
TEXT_COLOR = "#e0e0e0"
MUTED_COLOR = "#888"
BORDER_COLOR = "#2a2a4a"


def get_today_str() -> str:
    """Get today's date in China time as YYYY-MM-DD."""
    return datetime.now(CHINA_TZ).strftime("%Y-%m-%d")


def get_today_display() -> str:
    """Get a human-readable date string in Chinese."""
    now = datetime.now(CHINA_TZ)
    weekdays = ["一", "二", "三", "四", "五", "六", "日"]
    return now.strftime(f"%Y 年 %m 月 %d 日 星期{weekdays[now.weekday()]}")


def extract_project_url(entry: dict) -> str | None:
    """Extract project page URL from entry or create appropriate link."""
    return entry.get("project_page_url") or None


def generate_html(today_str: str, today_display: str, papers: list[dict]) -> str:
    """Generate the main HTML page."""
    cards_html = []
    for i, paper in enumerate(papers, 1):
        summary = paper.get("chinese_summary", {})
        task = summary.get("task_setting", "")
        motivation = summary.get("motivation", "")
        solution = summary.get("solution", "")

        proj_url = extract_project_url(paper)

        # Build links
        links_html = f"""
            <div class="paper-links">
                <a href="{paper['arxiv_url']}" class="link-btn" target="_blank">📄 arXiv</a>
                <a href="{paper['pdf_url']}" class="link-btn" target="_blank">📥 PDF</a>"""

        if proj_url:
            links_html += f'\n                <a href="{proj_url}" class="link-btn project" target="_blank">🌐 Project Page</a>'

        links_html += "\n            </div>"

        card = f"""
        <div class="paper-card">
            <div class="paper-number">#{i}</div>
            <h2 class="paper-title">
                <a href="{paper['arxiv_url']}" target="_blank">{paper['title']}</a>
            </h2>
            <div class="paper-meta">{paper.get('category', '')}</div>
            <div class="paper-summary">
                <div class="summary-row">
                    <span class="summary-label">任务设定</span>
                    <span class="summary-text">{task}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">痛点动机</span>
                    <span class="summary-text">{motivation}</span>
                </div>
                <div class="summary-row">
                    <span class="summary-label">解决方案</span>
                    <span class="summary-text">{solution}</span>
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
            line-height: 1.6;
            min-height: 100vh;
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
            font-size: 1.8rem;
            color: {ACCENT_COLOR};
            margin-bottom: 8px;
            letter-spacing: 0.05em;
        }}
        header .subtitle {{
            font-size: 0.95rem;
            color: {MUTED_COLOR};
        }}
        header .subtitle a {{
            color: {ACCENT_COLOR};
            text-decoration: none;
        }}
        header .subtitle a:hover {{
            text-decoration: underline;
        }}
        .stats-bar {{
            text-align: center;
            margin-bottom: 30px;
            font-size: 0.9rem;
            color: {MUTED_COLOR};
        }}
        .paper-card {{
            background: {CARD_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            transition: border-color 0.2s, transform 0.2s;
            position: relative;
        }}
        .paper-card:hover {{
            border-color: {ACCENT_COLOR};
            transform: translateY(-2px);
        }}
        .paper-number {{
            position: absolute;
            top: 16px;
            right: 20px;
            font-size: 1.5rem;
            font-weight: 700;
            color: {BORDER_COLOR};
            opacity: 0.5;
        }}
        .paper-title {{
            font-size: 1.1rem;
            margin-bottom: 8px;
            padding-right: 40px;
        }}
        .paper-title a {{
            color: {TEXT_COLOR};
            text-decoration: none;
        }}
        .paper-title a:hover {{
            color: {ACCENT_COLOR};
        }}
        .paper-meta {{
            font-size: 0.8rem;
            color: {ACCENT_COLOR};
            margin-bottom: 16px;
            display: inline-block;
            background: rgba(124, 92, 191, 0.1);
            padding: 2px 10px;
            border-radius: 4px;
        }}
        .paper-summary {{
            margin-bottom: 16px;
        }}
        .summary-row {{
            margin-bottom: 8px;
            display: flex;
            gap: 8px;
        }}
        .summary-label {{
            flex-shrink: 0;
            font-size: 0.8rem;
            font-weight: 600;
            color: {ACCENT_COLOR};
            background: rgba(124, 92, 191, 0.08);
            padding: 1px 8px;
            border-radius: 4px;
            min-width: 56px;
            text-align: center;
        }}
        .summary-text {{
            font-size: 0.9rem;
            color: #ccc;
        }}
        .paper-links {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .link-btn {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 0.85rem;
            text-decoration: none;
            transition: all 0.2s;
            background: rgba(124, 92, 191, 0.15);
            color: {ACCENT_COLOR};
            border: 1px solid transparent;
        }}
        .link-btn:hover {{
            background: rgba(124, 92, 191, 0.3);
            border-color: {ACCENT_COLOR};
        }}
        .link-btn.project {{
            background: rgba(76, 175, 80, 0.15);
            color: #66bb6a;
        }}
        .link-btn.project:hover {{
            background: rgba(76, 175, 80, 0.3);
            border-color: #66bb6a;
        }}
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
        }}
        .empty-state p {{
            font-size: 1.2rem;
            margin-bottom: 12px;
        }}
        .empty-state .hint {{
            font-size: 0.9rem;
            color: {MUTED_COLOR};
        }}
        footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid {BORDER_COLOR};
            font-size: 0.8rem;
            color: {MUTED_COLOR};
        }}
        @media (max-width: 600px) {{
            .container {{ padding: 20px 12px; }}
            header h1 {{ font-size: 1.4rem; }}
            .paper-card {{ padding: 16px; }}
            .paper-title {{ font-size: 1rem; }}
            .summary-row {{ flex-direction: column; gap: 2px; }}
            .summary-label {{ align-self: flex-start; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📄 Daily Paper Feed</h1>
            <div class="subtitle">
                {today_display} · 共 {len(papers)} 篇相关论文 ·
                <a href="archive/">📚 历史存档</a>
            </div>
        </header>

        <div class="stats-bar">
            来源：<a href="https://papers.cool/arxiv/cs.CV" target="_blank" style="color:{ACCENT_COLOR};">cs.CV</a>
            · <a href="https://papers.cool/arxiv/cs.AI" target="_blank" style="color:{ACCENT_COLOR};">cs.AI</a>
            · 通过 papers.cool 抓取
        </div>

        {papers_content}

        <footer>
            <p>Daily Paper Feed · 自动从 arXiv 抓取 · 基于研究兴趣筛选</p>
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
            line-height: 1.6;
            min-height: 100vh;
        }}
        .container {{
            max-width: 700px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        h1 {{
            color: {ACCENT_COLOR};
            margin-bottom: 8px;
        }}
        .back {{
            margin-bottom: 30px;
        }}
        .back a {{
            color: {ACCENT_COLOR};
            text-decoration: none;
            font-size: 0.9rem;
        }}
        .back a:hover {{
            text-decoration: underline;
        }}
        ul {{
            list-style: none;
        }}
        li {{
            margin-bottom: 10px;
        }}
        li a {{
            color: {TEXT_COLOR};
            text-decoration: none;
            font-size: 1rem;
            padding: 8px 16px;
            display: block;
            background: {CARD_COLOR};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            transition: all 0.2s;
        }}
        li a:hover {{
            border-color: {ACCENT_COLOR};
            color: {ACCENT_COLOR};
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="back"><a href="../">← 返回最新</a></div>
        <h1>📚 历史存档</h1>
        <p style="color: {MUTED_COLOR}; margin-bottom: 30px;">共 {len(archives)} 期</p>
        <ul>
            {''.join(items_html)}
        </ul>
    </div>
</body>
</html>"""


def main():
    papers = json.load(sys.stdin)
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
    # Update the back link in archive page
    archive_html = archive_html.replace(
        '<a href="archive/">📚 历史存档</a>',
        '<a href="index.html" class="archive-link">📚 全部存档</a>'
    )
    archive_html = archive_html.replace(
        '<a href="../">← 返回最新</a>',
        '<a href="../">← 返回最新</a>'
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

    # Add today to the list
    if today_str not in existing_archives:
        existing_archives.append(today_str)

    archive_index_html = generate_archive_index(existing_archives)
    archive_index_path = os.path.join(archive_dir, "index.html")
    with open(archive_index_path, "w", encoding="utf-8") as f:
        f.write(archive_index_html)
    print(f"  → archive/index.html ({len(existing_archives)} archives)", file=sys.stderr)

    # Also update the main page's archive link
    # (the archive page already has the correct link)

    # Print the page path for cron job to use
    print(f"\nPages generated at:", file=sys.stderr)
    print(f"  file://{index_path}", file=sys.stderr)
    print(f"  file://{archive_path}", file=sys.stderr)


if __name__ == "__main__":
    main()