# 概要：`backend/app/utils/text_utils.py`

**对应源码**：[../../../../../backend/app/utils/text_utils.py](../../../../../backend/app/utils/text_utils.py)

## 路径与角色

文本清洗、截断、Markdown 轻处理等（以实际函数为准）。

## 对外接口

纯函数工具。

## 关键依赖

无外部服务。

## 数据流 / 副作用

无。

## 与前端/其它模块的衔接

Agent 与 parser 可能复用。

## 注意点

与 LLM 提示边界（长度）协调。
