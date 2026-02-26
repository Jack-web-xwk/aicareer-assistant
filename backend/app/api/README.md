# api/

## 功能说明
API 路由层，定义所有 HTTP 和 WebSocket 接口，负责请求验证、响应格式化和路由分发。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- FastAPI Router
- Pydantic（请求/响应模型）
- services/（业务逻辑）
- core/（依赖注入）

## 文件说明
| 文件 | 说明 |
|------|------|
| __init__.py | 路由汇总注册 |
| resume.py | 简历相关接口 |
| interview.py | 面试模拟接口（含 WebSocket） |
| health.py | 健康检查接口 |

## 注意事项
- 所有接口需添加合适的 HTTP 状态码
- 错误响应使用统一的 JSON 格式
- WebSocket 接口需处理连接断开等异常
