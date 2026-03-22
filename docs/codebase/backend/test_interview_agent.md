# 概要：`backend/test_interview_agent.py`

**对应源码**：[../../../backend/test_interview_agent.py](../../../backend/test_interview_agent.py)

## 路径与角色

面试 Agent 冒烟/集成脚本：验证图或 LLM 调用链在本地可运行（以脚本实现为准）。

## 对外接口

`python test_interview_agent.py` 或 pytest。

## 关键依赖

[app/agents/interview_agent.md](app/agents/interview_agent.md)、`OPENAI_API_KEY`。

## 数据流 / 副作用

可能产生真实 LLM 调用与费用。

## 与前端/其它模块的衔接

间接验证 [app/api/interview.md](app/api/interview.md) 依赖的 Agent。

## 注意点

勿在 CI 无密钥环境强依赖真实 API；可加 mock。
