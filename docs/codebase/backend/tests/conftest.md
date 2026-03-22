# 概要：`backend/tests/conftest.py`

**对应源码**：[../../../../backend/tests/conftest.py](../../../../backend/tests/conftest.py)

## 路径与角色

Pytest fixtures：内存 SQLite 引擎、`AsyncClient`、覆盖 `get_db` 等，支撑 API 集成测试。

## 对外接口

`@pytest.fixture` 定义体。

## 关键依赖

`httpx`、`pytest-asyncio`、`app.core.database`、`settings`。

## 数据流 / 副作用

每测例独立 schema（以 scope 为准）。

## 与前端/其它模块的衔接

无。

## 注意点

fixtures scope 与异步 event_loop 配置需与项目 pytest 版本匹配。
