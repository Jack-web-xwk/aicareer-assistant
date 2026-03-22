# 概要：`backend/app/api/__init__.py`

**对应源码**：[../../../../../backend/app/api/__init__.py](../../../../../backend/app/api/__init__.py)

## 路径与角色

聚合子路由：`health`、`resume`、`interview`、`jobs`，挂载到统一 `APIRouter`。

## 对外接口

`router`，`include_router` 前缀 `/health`、`/resume`、`/interview`、`/jobs`（相对 `/api`）。

## 关键依赖

各子模块 `router`。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

前端 `/api/*` 路径与此对齐；见 [main.md](../../main.md)。

## 注意点

新增业务域应在此注册并保持 tag 一致便于 OpenAPI 分组。
