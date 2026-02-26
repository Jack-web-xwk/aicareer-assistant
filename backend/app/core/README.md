# core/

## 功能说明
核心配置和工具模块，包含应用配置、数据库连接、安全验证和依赖注入。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- pydantic-settings（配置管理）
- SQLAlchemy（数据库连接）
- python-dotenv（环境变量）

## 文件说明
| 文件 | 说明 |
|------|------|
| __init__.py | 模块初始化 |
| config.py | 应用配置（环境变量读取） |
| database.py | 数据库连接和会话管理 |
| dependencies.py | FastAPI 依赖注入 |
| exceptions.py | 自定义异常类 |

## 注意事项
- 敏感配置（如 API Key）必须通过环境变量读取
- 数据库会话需使用依赖注入，确保正确关闭
- 配置类使用 Pydantic Settings 进行验证
