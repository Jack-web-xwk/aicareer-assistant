# 概要：`backend/app/api/jobs.py`

**对应源码**：[../../../../../backend/app/api/jobs.py](../../../../../backend/app/api/jobs.py)

## 路径与角色

职位搜索聚合、单 URL 爬取入库、已保存职位 CRUD；接 [rate_limit.md](../core/rate_limit.md) 与 [aggregator.md](../services/job_search/aggregator.md)。

## 对外接口

`POST /search`、`POST /scrape-url`、`GET/POST/DELETE /saved` 等。

## 关键依赖

`SavedJob`、`UnifiedJobItem`、job_search 包、`job_scraper`、`get_db`。

## 数据流 / 副作用

外部站点列表/详情 HTTP；SQLite `saved_jobs`；限流内存状态。

## 与前端/其它模块的衔接

[JobsPage.md](../../../../../frontend/src/pages/JobsPage.md)、[SavedJobsPage.md](../../../../../frontend/src/pages/SavedJobsPage.md)、[TargetJobUrlPage.md](../../../../../frontend/src/pages/TargetJobUrlPage.md)。

## 注意点

爬虫稳定性与合规；429 与超时；`scrape-url` 可能较慢需前端长超时。
