# 概要：`backend/app/models/job_search_schemas.py`

**对应源码**：[../../../../../backend/app/models/job_search_schemas.py](../../../../../backend/app/models/job_search_schemas.py)

## 路径与角色

职位搜索专用 Schema：`JobSearchQuery`、`UnifiedJobItem`、`JobSearchResponse` 等与聚合结果结构。

## 对外接口

POST `/api/jobs/search` 的请求/响应模型。

## 关键依赖

Pydantic。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

[jobSearchStore.md](../../../../../frontend/src/stores/jobSearchStore.md)、[JobsPage.md](../../../../../frontend/src/pages/JobsPage.md)。

## 注意点

与 [normalize.md](../services/job_search/normalize.md) 输出结构一致。
