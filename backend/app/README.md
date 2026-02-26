# app/

## 功能说明
FastAPI 应用的核心代码目录，包含所有业务逻辑、API 路由、数据模型和 AI 智能体。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- FastAPI
- Pydantic
- SQLAlchemy
- LangGraph
- LangChain

## 子目录说明
| 目录 | 说明 |
|------|------|
| api/ | HTTP/WebSocket 路由定义 |
| core/ | 配置、安全、依赖注入 |
| models/ | SQLAlchemy ORM 模型和 Pydantic Schema |
| services/ | 业务逻辑服务层 |
| agents/ | LangGraph 智能体定义 |
| utils/ | 通用工具函数 |

## 注意事项
- 所有模块需遵循单一职责原则
- 服务层负责业务逻辑，API 层仅负责请求/响应处理
- 智能体模块需定义清晰的 State 和节点
