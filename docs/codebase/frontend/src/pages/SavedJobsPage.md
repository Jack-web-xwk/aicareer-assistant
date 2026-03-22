# 概要：`frontend/src/pages/SavedJobsPage.tsx`

**对应源码**：[../../../../../frontend/src/pages/SavedJobsPage.tsx](../../../../../frontend/src/pages/SavedJobsPage.tsx)

## 路径与角色

已保存职位列表：拉取 `GET /jobs/saved`、展示、删除等。

## 对外接口

默认导出页面组件。

## 关键依赖

[jobSavedApi](../services/api.md)、`antd`。

## 数据流 / 副作用

读删 SQLite 持久化记录。

## 与前端/其它模块的衔接

[jobs.md](../../../backend/app/api/jobs.md)；与 [TargetJobUrlPage.md](TargetJobUrlPage.md) 写入同源数据。

## 注意点

与统一 `SavedJobRecord` 类型字段一致。
