# Daily Paper Feed

从 papers.cool 抓取 arXiv 最新论文，根据研究兴趣筛选并生成中文摘要的 GitHub Pages 站点。

## 架构

```
scraper.py
filter.py
generator.py
run.sh
paperfeed_config.json
```

## 输出结构

```
index.html
archive/YYYY-MM-DD
```

## 配置

`paperfeed_config.json` 存放研究兴趣列表和数据源 URL，该文件已在 `.gitignore` 中，不会提交到云端。

## 运行

```bash
bash run.sh
bash run.sh YYYY-MM-DD
```