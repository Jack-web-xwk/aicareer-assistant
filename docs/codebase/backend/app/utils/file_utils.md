# 概要：`backend/app/utils/file_utils.py`

**对应源码**：[../../../../../backend/app/utils/file_utils.py](../../../../../backend/app/utils/file_utils.py)

## 路径与角色

文件路径、扩展名、安全文件名等辅助函数。

## 对外接口

工具函数集合。

## 关键依赖

`pathlib`/`os`。

## 数据流 / 副作用

可能读写小文件（以函数为准）。

## 与前端/其它模块的衔接

[resume.md](../api/resume.md) 上传保存路径。

## 注意点

路径穿越与权限校验。
