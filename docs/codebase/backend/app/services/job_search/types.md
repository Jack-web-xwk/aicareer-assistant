# 概要：`backend/app/services/job_search/types.py`

**对应源码**：[../../../../../../backend/app/services/job_search/types.py](../../../../../../backend/app/services/job_search/types.py)

## 路径与角色

职位搜索内部类型：各数据源原始条目、适配器协议用的 TypedDict/Protocol（以源码为准）。

## 对外接口

类型别名与数据结构定义。

## 关键依赖

`typing`、可能 `TypedDict`。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

经 [normalize.md](normalize.md) 与 [aggregator.md](aggregator.md) 间接影响 API 响应。

## 注意点

与 [job_search_schemas.md](../../models/job_search_schemas.md) 区分：此处偏内部管道。
