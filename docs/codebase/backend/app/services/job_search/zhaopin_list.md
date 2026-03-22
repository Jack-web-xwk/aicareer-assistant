# 概要：`backend/app/services/job_search/zhaopin_list.py`

**对应源码**：[../../../../../../backend/app/services/job_search/zhaopin_list.py](../../../../../../backend/app/services/job_search/zhaopin_list.py)

## 路径与角色

智联招聘列表数据源适配器。

## 对外接口

列表抓取/解析入口函数。

## 关键依赖

HTTP、解析逻辑、[types.md](types.md)。

## 数据流 / 副作用

出站 HTTP。

## 与前端/其它模块的衔接

[jobs.md](../../api/jobs.md) 多源合并之一。

## 注意点

与 Boss/鱼泡字段对齐靠 [normalize.md](normalize.md)。
