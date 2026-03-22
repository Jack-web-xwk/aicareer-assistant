# 概要：`backend/app/__init__.py`（含包级说明）

**对应源码**：[../../../../backend/app/__init__.py](../../../../backend/app/__init__.py)

## 路径与角色

后端应用包标识；仅导出 `__version__`，无业务逻辑。

## 对外接口

`__version__ = "1.0.0"`。

## 关键依赖

无。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

无。

## 注意点

版本号可能与 `core.config` 中 `APP_VERSION` 需人工保持一致。
