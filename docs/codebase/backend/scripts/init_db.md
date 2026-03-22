# 概要：`backend/scripts/init_db.py`

**对应源码**：[../../../../backend/scripts/init_db.py](../../../../backend/scripts/init_db.py)

## 路径与角色

命令行或脚本方式初始化/迁移数据库表（与 `main` lifespan 内 `create_tables` 互补或重复，以脚本内容为准）。

## 对外接口

`python -m` 或直接运行入口。

## 关键依赖

`database`、`Base`、模型导入。

## 数据流 / 副作用

创建/更新 SQLite 文件。

## 与前端/其它模块的衔接

无。

## 注意点

生产环境慎用自动删表；与 `add_resume_job_snapshot_column.sql` 等手工脚本配合。
