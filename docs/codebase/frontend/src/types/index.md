# 概要：`frontend/src/types/index.ts`

**对应源码**：[../../../../../frontend/src/types/index.ts](../../../../../frontend/src/types/index.ts)

## 路径与角色

全站 TypeScript 类型：`ApiResponse`、`ResumeInfo`、`JobSearchQuery`、`UnifiedJobItem`、`SavedJobRecord`、SSE 消息等。

## 对外接口

`export interface` / `type`。

## 关键依赖

无运行时依赖。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

[api.md](../services/api.md) 与各页面 props/state。

## 注意点

与后端 Pydantic 字段改名需同步；禁用 `any`（项目规范）。
