# 概要：`backend/app/services/job_search/boss_list.py`

**对应源码**：[../../../../../../backend/app/services/job_search/boss_list.py](../../../../../../backend/app/services/job_search/boss_list.py)

## 路径与角色

Boss 直聘（或兼容）列表页/接口适配：拉取列表并转为内部 types。

## 对外接口

异步/同步拉取函数，由 [aggregator.md](aggregator.md) 调度。

## 关键依赖

HTTP 客户端、HTML/JSON 解析。

## 数据流 / 副作用

出站请求；受站点可用性影响。

## 与前端/其它模块的衔接

[jobs.md](../../api/jobs.md) `POST /search` 数据源之一。

## 注意点

反爬与频率；字段变更需同步 normalize。
