# 概要：`frontend/src/pages/ResumeOptimizerPage.tsx`

**对应源码**：[../../../../../frontend/src/pages/ResumeOptimizerPage.tsx](../../../../../frontend/src/pages/ResumeOptimizerPage.tsx)

## 路径与角色

简历优化四步：上传或选择已有简历、填岗位 URL、LangGraph SSE 流式进度与 Markdown 预览、下载/复制；`?resumeId` / `?targetJobUrl` 深链恢复。

## 对外接口

默认导出页面组件；URL 查询参数。

## 关键依赖

[resumeApi](../services/api.md) upload/list/get、`optimizeStream`（fetch SSE）。

## 数据流 / 副作用

大流量 SSE token；轮询「优化中」兜底。

## 与前端/其它模块的衔接

[resume.md](../../../backend/app/api/resume.md)、[resume_optimizer_agent.md](../../../backend/app/agents/resume_optimizer_agent.md)。

## 注意点

节点 key 与后端一致；解析中轮询与 `streamActiveRef` 防重入。
