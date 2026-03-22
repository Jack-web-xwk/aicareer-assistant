# 概要：`frontend/src/pages/InterviewSimulatorPage.tsx`

**对应源码**：[../../../../../frontend/src/pages/InterviewSimulatorPage.tsx](../../../../../frontend/src/pages/InterviewSimulatorPage.tsx)

## 路径与角色

模拟面试 UI：选择岗位/技术栈/难度、语音或文本答题、进度与结束报告（以页面实现为准）。

## 对外接口

默认导出页面组件。

## 关键依赖

[interviewApi](../services/api.md)、可能的 Web Audio / MediaRecorder。

## 数据流 / 副作用

`interview/start`、逐题 `answer`、流式或轮询获取结果。

## 与前端/其它模块的衔接

[interview.md](../../../backend/app/api/interview.md)、[interview_agent.md](../../../backend/app/agents/interview_agent.md)。

## 注意点

浏览器麦克风权限；音频 Base64 体积。
