# 概要：`backend/app/models/user.py`

**对应源码**：[../../../../../backend/app/models/user.py](../../../../../backend/app/models/user.py)

## 路径与角色

`User` ORM：邮箱、用户名；与 `Resume`、`InterviewRecord` 等外键关联（以模型定义为准）。

## 对外接口

SQLAlchemy `User` 类及字段。

## 关键依赖

`Base`、`Resume` 等关系（避免循环导入时注意 lazy import）。

## 数据流 / 副作用

经 API `get_or_create_user` 写入。

## 与前端/其它模块的衔接

当前多为默认用户；无鉴权前端仍绑定该用户数据。

## 注意点

生产需替换为真实认证与用户隔离。
