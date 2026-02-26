# pages/

## 功能说明
页面组件目录，包含所有路由对应的页面组件。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- React 18
- Ant Design 5.x
- react-router-dom
- services/api.ts

## 文件说明
| 文件 | 说明 |
|------|------|
| HomePage.tsx | 首页 - 功能介绍和入口 |
| ResumeOptimizerPage.tsx | 简历优化页 - 上传、优化、下载 |
| InterviewSimulatorPage.tsx | 面试模拟页 - 配置、对话、报告 |

## 注意事项
- 页面组件负责状态管理和业务逻辑编排
- API 调用统一使用 services/api.ts
- 遵循 Ant Design 设计规范
