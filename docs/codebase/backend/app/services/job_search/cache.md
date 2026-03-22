# 概要：`backend/app/services/job_search/cache.py`

**对应源码**：[../../../../../../backend/app/services/job_search/cache.py](../../../../../../backend/app/services/job_search/cache.py)

## 路径与角色

进程内 TTL 缓存：降低重复搜索对外部站点的压力（以实现为准）。

## 对外接口

get/set 或装饰器式 API。

## 关键依赖

时间戳、查询参数哈希。

## 数据流 / 副作用

内存占用；多进程不共享。

## 与前端/其它模块的衔接

[aggregator.md](aggregator.md) 调用链上游/下游。

## 注意点

缓存键需包含城市、关键词、分页等维度。
