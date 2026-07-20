# Daily Paper Feed

从 papers.cool 抓取 arXiv 最新论文，根据研究兴趣筛选并生成中文摘要的 GitHub Pages 站点。

## 架构

```
scraper.py          → 从 papers.cool 拉取当天论文 HTML，解析为结构化数据
filter.py           → 调用 LLM 判断相关度，生成中文摘要
generator.py        → 生成 GitHub Pages 的 HTML
run.sh              → 入口脚本：scrape → filter → generate → commit & push
paperfeed_config.json → 本地配置（研究兴趣、数据源），**不提交到仓库**
```

## 输出结构

```
index.html          — 最新论文列表
archive/YYYY-MM-DD  — 每日存档页面
```

## 配置

`paperfeed_config.json` 存放研究兴趣列表和数据源 URL，该文件已在 `.gitignore` 中，不会提交到云端。

## 运行

```bash
bash run.sh                  # 使用 papers.cool 最新可用日期
bash run.sh YYYY-MM-DD       # 指定日期
```