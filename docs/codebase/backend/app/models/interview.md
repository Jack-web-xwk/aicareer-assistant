# 概要：`backend/app/models/interview.py`

**对应源码**：[../../../../../backend/app/models/interview.py](../../../../../backend/app/models/interview.py)

## 路径与角色

`InterviewRecord`（或同类）ORM：会话 id、岗位、技术栈、分数、报告正文、时间戳等。

## 对外接口

SQLAlchemy 模型字段与关系。

## 关键依赖

`User`、`Base`。

## 数据流 / 副作用

面试完成时由 interview API/Agent 持久化。

## 与前端/其它模块的衔接

[interview.md](../api/interview.md)；[InterviewSimulatorPage.md](../../../../../frontend/src/pages/InterviewSimulatorPage.md)、[ResumeHistoryPage.md](../../../../../frontend/src/pages/ResumeHistoryPage.md) 面试 Tab。

## 注意点

报告大文本存储与下载格式约定（如 Markdown）。
