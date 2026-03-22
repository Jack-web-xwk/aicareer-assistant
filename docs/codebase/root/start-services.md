# 概要：`start-services.ps1`（仓库根目录）

**对应源码**：[../../../start-services.ps1](../../../start-services.ps1)

## 路径与角色

PowerShell 菜单：选择启动后端、前端或组合；设置工作目录与环境（UTF-8 等）。

## 对外接口

在仓库根执行 `.\start-services.ps1`。

## 关键依赖

本机 `python`、`npm`、路径到 `backend`/`frontend`。

## 数据流 / 副作用

启动子进程监听端口（如 8000/5173）。

## 与前端/其它模块的衔接

与 [main.md](../backend/main.md)、Vite dev server 对应。

## 注意点

执行策略 `RemoteSigned`；代理与防火墙。
