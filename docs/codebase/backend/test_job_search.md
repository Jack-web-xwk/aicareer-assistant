# 概要：`backend/test_job_search.py`

**对应源码**：[../../../backend/test_job_search.py](../../../backend/test_job_search.py)

## 路径与角色

单元测试：`normalize`、聚合器合并/去重等职位搜索逻辑。

## 对外接口

`pytest` 收集的用例函数。

## 关键依赖

[app/services/job_search/normalize.md](app/services/job_search/normalize.md)、[app/services/job_search/aggregator.md](app/services/job_search/aggregator.md)。

## 数据流 / 副作用

无网络（若以 mock 为准）；本地断言。

## 与前端/其它模块的衔接

保障 [app/api/jobs.md](app/api/jobs.md) 行为稳定。

## 注意点

在 `backend` 目录执行 `pytest test_job_search.py`（或项目约定命令）。
