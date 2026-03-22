# 概要：`backend/app/services/resume_parser.py`

**对应源码**：[../../../../../backend/app/services/resume_parser.py](../../../../../backend/app/services/resume_parser.py)

## 路径与角色

解析 PDF/DOCX 为纯文本并可选结构化，供 LangGraph 提取节点使用。

## 对外接口

`parse_resume_file(path, type)` 等。

## 关键依赖

pdf 库、python-docx、可能 OCR（以代码为准）。

## 数据流 / 副作用

读本地上传文件；CPU 密集。

## 与前端/其它模块的衔接

[resume.md](../api/resume.md) 上传后后台任务或同步解析。

## 注意点

编码与版式复杂的简历可能解析质量差；大文件内存。
