# 概要：`backend/app/core/rate_limit.py`

**对应源码**：[../../../../../backend/app/core/rate_limit.py](../../../../../backend/app/core/rate_limit.py)

## 路径与角色

按客户端 IP 的简易滑动/计数限流，保护职位搜索等高频接口。

## 对外接口

可被 `jobs` 路由或依赖注入调用的限流函数/装饰器（以源码为准）。

## 关键依赖

`Request`（取 IP）、内存结构（进程内）。

## 数据流 / 副作用

超限返回 429；多进程部署时每实例独立计数。

## 与前端/其它模块的衔接

[jobs.md](../api/jobs.md) 的 search 接口；前端应处理 429 提示。

## 注意点

生产多副本时需换 Redis 等分布式限流若需全局一致。
