# 概要：`frontend/src/main.tsx`

**对应源码**：[../../../../frontend/src/main.tsx](../../../../frontend/src/main.tsx)

## 路径与角色

React 入口：`createRoot`、挂载 `App`、Ant Design `ConfigProvider`、路由 `BrowserRouter`（以源码为准）。

## 对外接口

无导出；启动脚本。

## 关键依赖

`react-dom/client`、`App.tsx`、全局样式。

## 数据流 / 副作用

无业务数据。

## 与前端/其它模块的衔接

全局主题与语言影响全部 [pages/](pages/) 下页面。

## 注意点

严格模式 `StrictMode` 对 effect 双调用行为。
