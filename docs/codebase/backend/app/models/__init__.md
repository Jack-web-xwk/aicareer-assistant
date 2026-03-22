# 概要：`backend/app/models/__init__.py`

**对应源码**：[../../../../../backend/app/models/__init__.py](../../../../../backend/app/models/__init__.py)

## 路径与角色

聚合导出 ORM（`User`、`Resume`、`InterviewRecord`、`SavedJob`）与常用 Pydantic schema，供 `from app.models import ...`。

## 对外接口

`__all__` 列表中的符号。

## 关键依赖

各子模块模型与 `schemas`。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

`database`/`main` 导入以注册 metadata；API 层引用 schema。

## 注意点

新增模型务必加入 `__all__` 并在 `create_tables` 路径中可发现。
