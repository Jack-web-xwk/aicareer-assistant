# 概要：`backend/app/core/database.py`

**对应源码**：[../../../../../backend/app/core/database.py](../../../../../backend/app/core/database.py)

## 路径与角色

SQLAlchemy 2.0 异步引擎、`AsyncSession` 工厂、`get_db` 依赖；`create_tables`；SQLite 迁移补丁 `ensure_sqlite_schema`。

## 对外接口

`Base`、`engine`、`AsyncSessionLocal`、`get_db()`、`create_tables()`、`ensure_sqlite_schema()`。

## 关键依赖

`settings.DATABASE_URL`、各 ORM 模型（需已导入以注册 metadata）。

## 数据流 / 副作用

所有经 `get_db` 的路由读写 SQLite（或配置的 DB）。

## 与前端/其它模块的衔接

API 层通过 `Depends(get_db)` 注入会话。

## 注意点

新增列/表时除 `create_tables` 外可能需 `ensure_sqlite_schema` 或独立 SQL 脚本。
