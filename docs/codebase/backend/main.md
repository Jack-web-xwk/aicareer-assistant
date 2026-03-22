# 概要：`backend/main.py`

**对应源码**：[../../../backend/main.py](../../../backend/main.py)

## 路径与角色

FastAPI 应用入口：生命周期、CORS、全局异常、挂载 `/api` 与静态资源。

## 对外接口

- ASGI 应用实例 `app`；`lifespan` 内启动时建表、补 SQLite 列、`UPLOAD_DIR` 与 `./data` 目录。

## 关键依赖

`settings`、`create_tables`、`ensure_sqlite_schema`、`register_exception_handlers`、`api_router`、`get_logger`。

## 数据流 / 副作用

启动时写 SQLite schema、创建目录；运行期通过路由处理 HTTP/SSE/WebSocket（由各子路由定义）。

## 与前端/其它模块的衔接

前端 Vite 代理 `/api` 至此服务；OpenAPI 文档路径 `/docs`。

## 注意点

CORS 来源来自 `settings.cors_origins_list`；静态文件挂载路径见文件末尾（若有）。
