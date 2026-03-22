# 概要：`backend/app/api/interview.py`

**对应源码**：[../../../../../backend/app/api/interview.py](../../../../../backend/app/api/interview.py)

## 路径与角色

模拟面试：开始会话、提交答案（文本/音频）、流式评估、历史列表、报告详情；调用 `InterviewAgent` 与 `audio_processor`。

## 对外接口

`POST /start`、`POST /{session}/answer`、`POST/GET .../stream`、`GET /history`、`GET /report` 等（以源码路由为准）。

## 关键依赖

`get_db`、`InterviewRecord`、`InterviewAgent`、`audio_processor`、LLM。

## 数据流 / 副作用

可选 Whisper/TTS 外部 API；持久化会话与报告。

## 与前端/其它模块的衔接

[InterviewSimulatorPage.md](../../../../../frontend/src/pages/InterviewSimulatorPage.md)、[ResumeHistoryPage.md](../../../../../frontend/src/pages/ResumeHistoryPage.md) 面试 Tab。

## 注意点

音频体积与 Base64 传输；WebSocket/SSE 与 REST 并存时注意前端实现。
