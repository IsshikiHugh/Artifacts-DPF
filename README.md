# DailyPaperFeed

GitHub Pages 上展示的每日论文推荐，从 papers.cool 抓取 cs.CV 和 cs.AI 领域的新论文，
根据研究兴趣筛选后生成中文摘要。

## 数据源

- https://papers.cool/arxiv/cs.CV — Computer Vision and Pattern Recognition
- https://papers.cool/arxiv/cs.AI — Artificial Intelligence
- 镜像 arXiv 的 announcement schedule（周日～周四更新）

## 研究兴趣（用于筛选）

- Human motion / pose estimation / mesh recovery (SMPL, human mesh)
- Human-scene interaction / 3D scene understanding
- Video generation / video diffusion models
- Embodied AI / robot learning / policy learning
- 3D human reconstruction / 4D human
- Egocentric vision / hand-object interaction
- MLLM reasoning / visual grounding
- Agent / tool-use / planning

## 架构

```
scraper.py          → 从 papers.cool 拉取当天论文 HTML，解析为结构化数据
filter.py           → 调用 LLM 判断每篇论文是否相关，保留感兴趣的
generator.py        → 生成 GitHub Pages 的 HTML
run.sh              → 入口脚本：scrape → filter → generate → commit & push
```

## 输出结构

```
index.html          — 最新论文列表（主页面）
archive/YYYY-MM-DD  — 每日存档页面
```

## 每篇论文的展示内容

- Title（英文标题 + arXiv 链接）
- 中文内容概括（task setting、motivation/痛点、solution，直白简洁）
- 相关资源链接（arXiv、project page、PDF）