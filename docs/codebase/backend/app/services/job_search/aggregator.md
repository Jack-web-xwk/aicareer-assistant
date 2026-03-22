# 概要：`backend/app/services/job_search/aggregator.py`

**对应源码**：[../../../../../../backend/app/services/job_search/aggregator.py](../../../../../../backend/app/services/job_search/aggregator.py)

## 路径与角色

并发/顺序调用各 list 适配器，合并、去重、排序、分页，配合 [cache.md](cache.md)。

## 对外接口

面向 `jobs` API 的单一入口函数（名称以源码为准）。

## 关键依赖

`boss_list`、`zhaopin_list`、`yupao_list`、`normalize`、`cache`。

## 数据流 / 副作用

多次出站 HTTP；CPU 合并。

## 与前端/其它模块的衔接

[jobs.md](../../api/jobs.md)；[jobSearchStore.md](../../../../../../frontend/src/stores/jobSearchStore.md)。

## 注意点

与 [rate_limit.md](../../core/rate_limit.md) 协同；失败单源降级策略。
