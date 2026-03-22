# frontend/

## 功能说明
前端应用目录，使用 React 18 + TypeScript + Ant Design 构建用户界面。

## 开发状态
- [ ] 待开发
- [x] 开发中
- [ ] 已完成

## 依赖关系
- React 18
- TypeScript
- Ant Design 5.x
- Zustand（职位搜索筛选与历史等本地状态）
- Vite（构建工具）
- Axios（HTTP 请求）

## 目录结构
```
frontend/
├── src/
│   ├── pages/           # 页面组件
│   ├── components/      # 通用组件
│   ├── services/        # API 调用服务
│   ├── hooks/           # 自定义 Hooks
│   ├── types/           # TypeScript 类型定义
│   └── utils/           # 工具函数
├── public/              # 静态资源
├── package.json         # 依赖配置
├── tsconfig.json        # TypeScript 配置
└── vite.config.ts       # Vite 配置
```

## 开发命令
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 注意事项
- 组件使用函数式组件 + Hooks
- 状态管理：简历/面试等可用 Context；**职位搜索**使用 `src/stores/jobSearchStore.ts`（Zustand + 搜索历史持久化）
- API 调用统一封装在 services 目录；`jobSearchApi.search` 支持 `AbortSignal` 取消上一次请求
- 所有组件和函数需添加 TypeScript 类型
- 职位搜索页 `/jobs` 依赖后端 `POST /api/jobs/search`；后端对搜索接口有 **每 IP 每分钟 10 次** 限流，频繁请求将返回 429
