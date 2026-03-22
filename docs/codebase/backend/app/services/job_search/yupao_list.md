# 概要：`backend/app/services/job_search/yupao_list.py`

**对应源码**：[../../../../../../backend/app/services/job_search/yupao_list.py](../../../../../../backend/app/services/job_search/yupao_list.py)

## 路径与角色

鱼泡网等数据源列表适配器。

## 对外接口

列表拉取与解析函数。

## 关键依赖

HTTP、[types.md](types.md)。

## 数据流 / 副作用

出站请求。

## 与前端/其它模块的衔接

[jobs.md](../../api/jobs.md) 聚合搜索。

## 注意点

源站结构变化时需回归 [test_job_search.md](../../../test_job_search.md)。
