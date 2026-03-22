# 概要：`frontend/src/pages/ResumeHistoryPage.tsx`

**对应源码**：[../../../../../frontend/src/pages/ResumeHistoryPage.tsx](../../../../../frontend/src/pages/ResumeHistoryPage.tsx)

## 路径与角色

统一历史：简历任务表（状态、岗位快照、继续/解锁/删除）与面试报告表；Drawer 详情与 Markdown 渲染。

## 对外接口

默认导出页面组件。

## 关键依赖

[resumeApi](../services/api.md)、[interviewApi](../services/api.md)、`antd` Table/Drawer。

## 数据流 / 副作用

`GET /resume/history`、`GET /interview/history`、详情与下载。

## 与前端/其它模块的衔接

[resume.md](../../../backend/app/api/resume.md)、[interview.md](../../../backend/app/api/interview.md)。

## 注意点

`items` 防御性处理与空态；外链 `job_snapshot.source_url`。
