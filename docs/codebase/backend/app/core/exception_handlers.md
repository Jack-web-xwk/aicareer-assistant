# 概要：`backend/app/core/exception_handlers.py`

**对应源码**：[../../../../../backend/app/core/exception_handlers.py](../../../../../backend/app/core/exception_handlers.py)

## 路径与角色

注册 FastAPI 全局异常处理器：422、`HTTPException`、未捕获 `Exception`，统一写日志并返回 JSON。

## 对外接口

`register_exception_handlers(app: FastAPI)`。

## 关键依赖

`app.utils.logger`。

## 数据流 / 副作用

错误时写应用日志文件/控制台；返回 `JSONResponse`。

## 与前端/其它模块的衔接

前端 axios 拦截器可解析 `detail` 字段；与 [../../../../../frontend/src/services/api.md](../../../../../frontend/src/services/api.md) 错误展示相关。

## 注意点

处理器注册顺序需满足 FastAPI/Starlette 约定（先具体后通用）。
