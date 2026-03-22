# 概要：`backend/app/api/health.py`

**对应源码**：[../../../../../backend/app/api/health.py](../../../../../backend/app/api/health.py)

## 路径与角色

健康检查端点，供负载均衡或脚本探测服务存活。

## 对外接口

GET `/api/health/...`（具体路径以路由为准）。

## 关键依赖

无重依赖。

## 数据流 / 副作用

通常只返回静态 JSON。

## 与前端/其它模块的衔接

可选被运维或 [start-services.md](../../../root/start-services.md) 探测。

## 注意点

勿在此做重计算或外部依赖检查，除非明确需要深度探活。
