# 概要：`backend/app/services/audio_processor.py`

**对应源码**：[../../../../../backend/app/services/audio_processor.py](../../../../../backend/app/services/audio_processor.py)

## 路径与角色

面试音频：Base64 解码、Whisper 转写、可选 TTS 合成（以实际函数为准）。

## 对外接口

供 [interview.md](../api/interview.md) 调用的处理函数。

## 关键依赖

OpenAI Whisper API 或本地 whisper、设置中的 API Key。

## 数据流 / 副作用

出站 API；临时文件或内存缓冲。

## 与前端/其它模块的衔接

[InterviewSimulatorPage.md](../../../../../frontend/src/pages/InterviewSimulatorPage.md) 录音上传。

## 注意点

费用与延迟；音频格式与采样率约定。
