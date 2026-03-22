# 概要：`backend/app/models/resume.py`

**对应源码**：[../../../../../backend/app/models/resume.py](../../../../../backend/app/models/resume.py)

## 路径与角色

`Resume` ORM：文件路径、解析状态、岗位 URL/标题、`job_snapshot` JSON 文本、优化结果、`match_analysis` 等。

## 对外接口

`Resume` 模型、`ResumeStatus` 枚举。

## 关键依赖

`User` 外键、`Base`。

## 数据流 / 副作用

上传、解析、LangGraph 优化全生命周期更新本表。

## 与前端/其它模块的衔接

[resume.md](../api/resume.md) CRUD 与 SSE；[ResumeOptimizerPage.md](../../../../../frontend/src/pages/ResumeOptimizerPage.md)。

## 注意点

大字段（正文、优化结果）注意 SQLite 性能；`job_snapshot` 与展示字段对齐。
