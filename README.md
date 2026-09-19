# cook-videos

村驴（Bilibili MID `417298480`）公开视频元数据、可追溯菜谱基础表和静态检索页面。

## 数据分层

- `村驴/raw.json`：爬虫原始字段的稳定归档；以 BV 号增量合并，不由标记程序改写。
- `村驴/videos.json`：保留原始字段并增加 `labeler_version`、`dish_names`。修改规则后提升 `scripts/label.py` 的 `VERSION`，运行时会全量重标。
- `base/dishes.json`：以规范菜名为 key，记录食材、特殊工具和来源路径。
- `base/ingredients.json`：以规范食材名为 key，记录处理方法、备注和来源。
- `base/*_alias_groups.json`：别名组；可用简洁 list，也支持 `{ "canonical": "规范名", "names": [...] }`。
- `reference/howtocook-recipes.txt`：参考仓库原文的可审计文本快照。其来源、许可、抓取和转换程序记录于 `reference/source_manifest.json`。

菜表中的每种食材必须已存在于食材表，`scripts/validate.py` 会强制检查这项外键约束。

## 本地运行

```bash
python -m pip install -r requirements.txt
python scripts/bilibili.py          # 增量
python scripts/bilibili.py --full   # 全量刷新视频元数据
python scripts/fetch_reference.py   # GitHub → reference txt
python scripts/build_base.py        # txt → base JSON
python scripts/label.py
python scripts/validate.py
python -m http.server 8000
```

访问 `http://localhost:8000/site/`。若 Bilibili 对匿名请求限流，可在仓库 Actions Secret 中配置 `BILIBILI_COOKIE`；请勿把 Cookie 写进仓库。

## 自动化

`Update video data` 每周一 03:23 UTC 增量抓取、全量标记、校验并提交。`Rebuild base reference` 仅手动运行，避免每周无意义下载完整参考语料。`Deploy Pages` 在 main 更新后发布站点。

数据仅包含公开元数据；封面保留源站 URL，不复制视频或图片。Bilibili 接口并非稳定公共合同，脚本对错误显式失败，避免把空结果覆盖为“成功”。
