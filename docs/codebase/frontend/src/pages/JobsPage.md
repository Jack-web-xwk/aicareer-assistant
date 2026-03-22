# 概要：`frontend/src/pages/JobsPage.tsx`

**对应源码**：[../../../../../frontend/src/pages/JobsPage.tsx](../../../../../frontend/src/pages/JobsPage.tsx)

## 路径与角色

多源职位搜索 UI：筛选、排序、分页、卡片列表、空态；绑定 [jobSearchStore.md](../stores/jobSearchStore.md)。

## 对外接口

默认导出页面组件。

## 关键依赖

`jobSearchApi`/`store`、`antd` Table/Card。

## 数据流 / 副作用

搜索、可选保存职位（`jobSavedApi`）。

## 与前端/其它模块的衔接

后端 [jobs.md](../../../backend/app/api/jobs.md)；[SavedJobsPage.md](SavedJobsPage.md) 跳转。

## 注意点

取消请求与加载态；限流提示。
