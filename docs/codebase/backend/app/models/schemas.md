# 概要：`backend/app/models/schemas.py`

**对应源码**：[../../../../../backend/app/models/schemas.py](../../../../../backend/app/models/schemas.py)

## 路径与角色

Pydantic 模型：`SuccessResponse`/`ErrorResponse`、简历/面试请求响应体、`JobRequirements`、`MatchAnalysis` 等与 API 契约。

## 对外接口

各 `BaseModel` 子类；路由 `response_model` 引用。

## 关键依赖

Pydantic v2、`Field` 等。

## 数据流 / 副作用

仅校验与序列化，无 IO。

## 与前端/其它模块的衔接

与 [types/index.md](../../../../../frontend/src/types/index.md) 类型应对齐。

## 注意点

变更字段需同步前端类型与迁移。
