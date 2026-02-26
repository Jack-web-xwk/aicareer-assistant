# types/

## 功能说明
TypeScript 类型定义目录，定义所有 API 响应和组件使用的类型。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- 无外部依赖

## 文件说明
| 文件 | 说明 |
|------|------|
| index.ts | 所有类型定义的集中导出 |

## 主要类型
- `ApiResponse<T>` - API 响应通用类型
- `ResumeInfo` - 简历信息
- `ExtractedResumeInfo` - 提取的简历结构化信息
- `MatchAnalysis` - 匹配分析结果
- `InterviewSession` - 面试会话
- `InterviewReport` - 面试报告
- `WSMessage` - WebSocket 消息

## 注意事项
- 所有类型需与后端 Pydantic Schema 保持一致
- 禁止使用 `any` 类型
- 复杂类型应添加注释说明
