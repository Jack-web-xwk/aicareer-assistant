# 概要：`backend/app/models/saved_job.py`

**对应源码**：[../../../../../backend/app/models/saved_job.py](../../../../../backend/app/models/saved_job.py)

## 路径与角色

`SavedJob` ORM：统一保存「搜索收藏」与「URL 爬取」归一后的职位快照，含来源、原始 JSON 等（以字段为准）。

## 对外接口

`SavedJob` 模型。

## 关键依赖

`Base`、可能与 `User` 关联。

## 数据流 / 副作用

[jobs.md](../api/jobs.md) POST saved、scrape-url 写入。

## 与前端/其它模块的衔接

[SavedJobsPage.md](../../../../../frontend/src/pages/SavedJobsPage.md)、[TargetJobUrlPage.md](../../../../../frontend/src/pages/TargetJobUrlPage.md)。

## 注意点

与 Pydantic `UnifiedJobItem` 字段对齐，避免序列化丢失。
