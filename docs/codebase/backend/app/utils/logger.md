# 概要：`backend/app/utils/logger.py`

**对应源码**：[../../../../../backend/app/utils/logger.py](../../../../../backend/app/utils/logger.py)

## 路径与角色

统一日志：`get_logger(name)`，配置文件与控制台双通道（以实现为准）。

## 对外接口

`get_logger`。

## 关键依赖

`settings.LOG_LEVEL`、日志目录 `logs/`。

## 数据流 / 副作用

写磁盘日志文件。

## 与前端/其它模块的衔接

无直接衔接；运维查错。

## 注意点

`logs/` 应在 .gitignore；敏感信息勿打全量请求体。
