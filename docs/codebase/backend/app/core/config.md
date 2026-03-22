# 概要：`backend/app/core/config.py`

**对应源码**：[../../../../../backend/app/core/config.py](../../../../../backend/app/core/config.py)

## 路径与角色

Pydantic Settings：应用名、版本、数据库 URL、上传目录、OpenAI/兼容基址、CORS、日志级别等。

## 对外接口

单例 `settings`；派生属性如 `cors_origins_list`、`max_upload_size_bytes`。

## 关键依赖

`pydantic-settings`、环境变量 `.env`。

## 数据流 / 副作用

进程启动时读环境；无网络。

## 与前端/其它模块的衔接

CORS 控制浏览器来源；`UPLOAD_DIR` 与简历上传路径一致。

## 注意点

敏感项 `OPENAI_API_KEY` 勿提交；多环境用不同 `.env`。
