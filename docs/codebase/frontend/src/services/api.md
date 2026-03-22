# 概要：`frontend/src/services/api.ts`

**对应源码**：[../../../../../frontend/src/services/api.ts](../../../../../frontend/src/services/api.ts)

## 路径与角色

Axios 实例（`/api` baseURL、超时、错误拦截）、`resumeApi`、`interviewApi`、`jobSearchApi`、`jobSavedApi`、`jobScrapeApi`、`checkHealth`。

## 对外接口

各命名空间异步方法；简历/面试 SSE 使用 `fetch` 直连 `/api/.../stream`。

## 关键依赖

`../types`、浏览器 `fetch`（流式）。

## 数据流 / 副作用

HTTP 至后端；长超时用于爬取/AI。

## 与前端/其它模块的衔接

所有 [pages/](pages/) 的数据层入口。

## 注意点

错误 `detail` 可能为数组（FastAPI 422）；与后端 [exception_handlers.md](../../../backend/app/core/exception_handlers.md) 对齐。
