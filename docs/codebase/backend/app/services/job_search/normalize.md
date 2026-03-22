# 概要：`backend/app/services/job_search/normalize.py`

**对应源码**：[../../../../../../backend/app/services/job_search/normalize.py](../../../../../../backend/app/services/job_search/normalize.py)

## 路径与角色

将各源原始字段映射为统一的 `UnifiedJobItem` 形状：标题、公司、薪资、链接、来源等。

## 对外接口

纯函数 `normalize_*`（以源码为准）。

## 关键依赖

[types.md](types.md)、Pydantic/字典。

## 数据流 / 副作用

无 IO。

## 与前端/其它模块的衔接

[jobs.md](../../api/jobs.md) 搜索响应字段一致性。

## 注意点

URL 归一化与去重键（id）策略。
