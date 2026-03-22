# 概要：`backend/app/services/job_search/__init__.py`

**对应源码**：[../../../../../../backend/app/services/job_search/__init__.py](../../../../../../backend/app/services/job_search/__init__.py)

## 路径与角色

子包导出：对外暴露聚合函数或类型，简化 `from app.services.job_search import ...`。

## 对外接口

`__all__` 或隐式导出符号。

## 关键依赖

`aggregator` 等子模块。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

仅通过 [jobs.md](../../api/jobs.md) 间接使用。

## 注意点

保持公共 API 稳定，内部模块可自由重构。
