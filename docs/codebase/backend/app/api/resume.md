# 概要：`backend/app/api/resume.py`

**对应源码**：[../../../../../backend/app/api/resume.py](../../../../../backend/app/api/resume.py)

## 路径与角色

简历全生命周期：上传、解析、优化（同步/流式 SSE）、列表、历史总览、详情、下载、删除、解锁「优化中」；整合 `job_scraper` 与 `ResumeOptimizerAgent`。

## 对外接口

`/upload`、`/optimize/{id}`、`/optimize/{id}/stream`、`GET/DELETE /{id}`、`/history`、`/list`、`/download` 等。

## 关键依赖

`get_db`、`Resume`、`parse_resume_file`、`scrape_job_info`、`ResumeOptimizerAgent`、`SuccessResponse`。

## 数据流 / 副作用

文件写入 `UPLOAD_DIR`；SQLite 更新；SSE 流式写 token；外部 HTTP 爬岗位。

## 与前端/其它模块的衔接

[api.md](../../../../../frontend/src/services/api.md) `resumeApi`；[ResumeOptimizerPage.md](../../../../../frontend/src/pages/ResumeOptimizerPage.md)、[ResumeHistoryPage.md](../../../../../frontend/src/pages/ResumeHistoryPage.md)。

## 注意点

大文件与超时；SSE 与轮询并存时的状态一致性；默认用户隔离。
