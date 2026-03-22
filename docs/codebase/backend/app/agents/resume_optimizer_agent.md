# 概要：`backend/app/agents/resume_optimizer_agent.py`

**对应源码**：[../../../../../backend/app/agents/resume_optimizer_agent.py](../../../../../backend/app/agents/resume_optimizer_agent.py)

## 路径与角色

LangGraph 简历优化工作流：提取简历、分析 JD、匹配、流式生成 Markdown；节点事件映射到 SSE。

## 对外接口

`ResumeOptimizerAgent` 与 `stream_optimize`/`run` 类方法。

## 关键依赖

[llm_provider.md](../core/llm_provider.md)、[job_scraper.md](../services/job_scraper.md) 数据（经 API 注入 JD 文本）。

## 数据流 / 副作用

LLM 多轮；流式 token 经 API 推前端。

## 与前端/其它模块的衔接

[resume.md](../api/resume.md) `/optimize/.../stream`；[ResumeOptimizerPage.md](../../../../../frontend/src/pages/ResumeOptimizerPage.md)。

## 注意点

图节点名与前端 `GRAPH_NODES` 必须一致；失败时状态落库 `failed`。
