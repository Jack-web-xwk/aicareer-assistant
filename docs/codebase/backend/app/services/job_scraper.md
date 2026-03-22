# 概要：`backend/app/services/job_scraper.py`

**对应源码**：[../../../../../backend/app/services/job_scraper.py](../../../../../backend/app/services/job_scraper.py)

## 路径与角色

同步抓取招聘详情页（Boss 等），解析为 `JobRequirements` 结构，供简历优化与岗位快照。

## 对外接口

`scrape_job_info(url)` 等（以导出函数为准）。

## 关键依赖

`httpx`/`requests`、HTML 解析、可能 `asyncio` 线程池（若在 API 中 `run_in_executor`）。

## 数据流 / 副作用

出站 HTTP；延迟与反爬风险。

## 与前端/其它模块的衔接

[resume.md](../api/resume.md) 优化链路；[jobs.md](../api/jobs.md) `scrape-url`。

## 注意点

站点改版易碎；需合理 timeout 与 User-Agent；遵守 robots/使用条款。
