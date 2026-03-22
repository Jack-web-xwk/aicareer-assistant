# 概要：`backend/app/core/llm_provider.py`

**对应源码**：[../../../../../backend/app/core/llm_provider.py](../../../../../backend/app/core/llm_provider.py)

## 路径与角色

统一创建 Chat 模型、兼容 OpenAI 与 OpenAI-兼容基址（如国内代理）；供 Agent 与流式接口使用。

## 对外接口

工厂函数/类：返回 `ChatOpenAI` 或 LangChain 兼容实例（以源码导出名为准）。

## 关键依赖

`settings.OPENAI_API_KEY`、`OPENAI_BASE_URL`、langchain-openai。

## 数据流 / 副作用

调用外部 LLM HTTP API；计费与延迟受模型与网络影响。

## 与前端/其它模块的衔接

[resume_optimizer_agent.md](../agents/resume_optimizer_agent.md)、[interview_agent.md](../agents/interview_agent.md) 及 [resume.md](../api/resume.md) SSE、[interview.md](../api/interview.md)。

## 注意点

密钥缺失时尽早失败；流式需正确配置 timeout 与错误映射。
