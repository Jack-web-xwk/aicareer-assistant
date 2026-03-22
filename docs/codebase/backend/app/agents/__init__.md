# 概要：`backend/app/agents/__init__.py`

**对应源码**：[../../../../../backend/app/agents/__init__.py](../../../../../backend/app/agents/__init__.py)

## 路径与角色

Agent 子包导出或占位。

## 对外接口

`InterviewAgent`、`ResumeOptimizerAgent` 等（若 re-export）。

## 关键依赖

子模块。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

仅 API 层引用。

## 注意点

避免在 `__init__` 中做重导入副作用。
