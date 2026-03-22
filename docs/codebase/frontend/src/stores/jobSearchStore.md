# 概要：`frontend/src/stores/jobSearchStore.ts`

**对应源码**：[../../../../../frontend/src/stores/jobSearchStore.ts](../../../../../frontend/src/stores/jobSearchStore.ts)

## 路径与角色

Zustand：搜索关键词、城市、分页、结果列表、排序、历史查询、`AbortController` 取消进行中的 search。

## 对外接口

`useJobSearchStore` hook 与 actions。

## 关键依赖

[jobSearchApi](../services/api.md)、[types](../types/index.md)。

## 数据流 / 副作用

调用 `POST /api/jobs/search`。

## 与前端/其它模块的衔接

[JobsPage.md](../pages/JobsPage.md)。

## 注意点

防抖与 signal 避免竞态；429/超时错误提示。
