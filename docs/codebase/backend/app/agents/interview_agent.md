# 概要：`backend/app/agents/interview_agent.py`

**对应源码**：[../../../../../backend/app/agents/interview_agent.py](../../../../../backend/app/agents/interview_agent.py)

## 路径与角色

LangGraph/LangChain 编排模拟面试：出题、评估、生成报告；封装 LLM 调用与状态机。

## 对外接口

类 `InterviewAgent` 及 `start`、`submit`、`finish` 等（以源码为准）。

## 关键依赖

[llm_provider.md](../core/llm_provider.md)、提示词、可选工具。

## 数据流 / 副作用

多次 LLM 调用；可能长上下文。

## 与前端/其它模块的衔接

[interview.md](../api/interview.md)。

## 注意点

Token 消耗与超时；流式与同步路径一致性。
