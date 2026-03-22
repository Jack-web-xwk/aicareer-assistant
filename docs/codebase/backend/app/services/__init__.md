# 概要：`backend/app/services/__init__.py`

**对应源码**：[../../../../../backend/app/services/__init__.py](../../../../../backend/app/services/__init__.py)

## 路径与角色

服务层包初始化；可能导出常用服务符号或留空。

## 对外接口

包级 import 约定。

## 关键依赖

子模块 `job_scraper`、`resume_parser` 等。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

被 API 与 Agent 引用。

## 注意点

避免循环导入（服务 ↔ API ↔ Agent）。
