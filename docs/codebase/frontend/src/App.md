# 概要：`frontend/src/App.tsx`

**对应源码**：[../../../../frontend/src/App.tsx](../../../../frontend/src/App.tsx)

## 路径与角色

布局、导航、`Routes` 注册：首页、职位搜索、保存职位、目标 URL、简历优化、历史、面试等。

## 对外接口

默认导出 `App` 组件。

## 关键依赖

`react-router-dom`、各 `pages/*`。

## 数据流 / 副作用

无全局 store（职位搜索用 zustand 在子树）。

## 与前端/其它模块的衔接

路径与 [api.md](services/api.md) 中 `/api` 前缀配合 Vite 代理。

## 注意点

新增页面需同时加菜单与 `Route`。
