# 概要：`backend/app/core/exceptions.py`

**对应源码**：[../../../../../backend/app/core/exceptions.py](../../../../../backend/app/core/exceptions.py)

## 路径与角色

应用级异常层次：`AppException`、`NotFoundException`、`FileProcessingException` 等，带 `to_dict()` 供统一错误 JSON。

## 对外接口

异常类定义；业务层 `raise` 后由中间件或路由捕获（视项目用法）。

## 关键依赖

无外部服务。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

若路由显式转换，则影响前端错误结构。

## 注意点

与 Starlette `HTTPException` 并存时需统一处理策略。
