# 概要：`backend/app/core/dependencies.py`

**对应源码**：[../../../../../backend/app/core/dependencies.py](../../../../../backend/app/core/dependencies.py)

## 路径与角色

FastAPI 依赖：`get_database_session`（封装 `get_db`）、`get_openai_api_key`、`get_upload_dir`、`get_max_upload_size`；内含简单 `RateLimiter` 类。

## 对外接口

上述可 `Depends()` 的函数与类。

## 关键依赖

`get_db`、`settings`。

## 数据流 / 副作用

`get_openai_api_key` 在缺失配置时抛 `ValueError`。

## 与前端/其它模块的衔接

路由中注入 DB 与配置边界。

## 注意点

与 [rate_limit.md](rate_limit.md) 的限流实现可能并存，勿混淆两套策略。
