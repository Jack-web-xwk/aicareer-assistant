# services/

## 功能说明
API 服务层，封装所有与后端的 HTTP/WebSocket 通信。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- axios
- types/

## 文件说明
| 文件 | 说明 |
|------|------|
| api.ts | API 客户端和所有接口封装 |

## 使用示例
```typescript
import { resumeApi, interviewApi } from './services/api'

// 上传简历
const response = await resumeApi.upload(file)

// 开始面试
const session = await interviewApi.start({
  job_role: 'Python 后端工程师',
  tech_stack: ['Python', 'FastAPI'],
  difficulty_level: 'medium',
})
```

## 注意事项
- 所有 API 调用都经过统一的错误处理
- 超时设置为 60 秒（AI 操作可能较慢）
- WebSocket 用于实时面试交互
