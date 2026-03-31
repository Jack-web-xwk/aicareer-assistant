# 前端架构分析报告 - Pod C: 面试体验增强

## 1. 现有组件架构

### InterviewSimulatorPage 状态机

当前 InterviewSimulatorPage.tsx 采用单一组件多阶段管理模式。

**状态转换流程：**
SETUP -> INTERVIEW -> REPORT

**核心状态变量：**
- stage: 'setup' | 'interview' | 'report' - 控制主流程
- session: InterviewSession | null - 面试会话信息
- messages: ChatMessage[] - 对话历史（本地临时）
- report: InterviewReport | null - 评估报告
- wsRef: WebSocket | null - 实时连接

**痛点分析：**
1. 无面试前准备：setup 阶段仅有基础表单，缺少题库预览、模式选择
2. 无面试后回放：conversation_history 未持久化展示，无法时间轴拖拽
3. 无进度追踪：缺少跨 session 的数据聚合和可视化
4. 状态耦合：所有逻辑集中在单组件，难以复用

### 可复用组件清单

| 组件名 | 功能 | 复用场景 |
|--------|------|----------|
| TechStackSelector | 技术栈多选 | 准备模式、职位搜索 |
| DifficultySelector | 难度选择器 | 准备模式、学习模块 |
| ChatMessageList | 对话气泡列表 | 面试中、回放、练习模式 |
| ScoreCircle | 圆形进度分 | 报告页、Dashboard、回放 |
| StrengthWeaknessList | 优势/不足对比 | 报告页、Dashboard |
| MarkdownReportViewer | Markdown 渲染 | 详细报告、学习文章 |

建议抽取位置：frontend/src/components/interview/

### 状态管理方式分析

当前方案：Zustand + Local State 混合

1. Zustand Store (jobSearchStore.ts)
   - 优点：用于职位搜索的复杂筛选状态，支持持久化
   - 支持历史记录管理，支持 AbortController 取消请求

2. Local State (InterviewSimulatorPage.tsx)
   - 缺点：所有面试状态在组件内，无法跨页面共享
   - 刷新后状态丢失

推荐方案：新建 interviewStore.ts，使用 Zustand 统一管理

## 2. UI/UX 改进机会

### 2.1 准备模式入口设计 (/interview/prep)

功能要点：
- 展示用户统计数据（已完成 X 次模拟，平均分）
- 岗位选择表单
- 技术栈多选
- 面试模式选择（练习/模拟/挑战）
- 题库预览（随机 3-5 题）
- 时间限制设置

关键交互：
- 模式选择卡片：hover 显示详细说明
- 题库预览：点击展开完整题库
- 时间限制滑块：15/30/45 分钟快捷选项

### 2.2 回放功能交互流程 (/interview/replay/:sessionId)

数据来源：GET /api/interview/{id}/replay (需新增)

核心功能：
- 时间轴拖拽：快速定位到某个问题节点
- 对话气泡展示：区分角色，显示时间戳
- 即时反馈：每个问题下方显示当时评分
- 重新回答：对比两次表现（A/B 测试 UI）

### 2.3 进度 Dashboard 布局 (/progress)

数据来源：GET /api/user/progress/dashboard (需新增)

可视化指标：
- 总面试次数（统计卡片）
- 平均分趋势（折线图 + 柱状图）
- 能力雷达图（五维：技术/沟通/逻辑/表达/潜力）
- 技术栈掌握度（热力图或条形图）
- 最近面试记录（列表）

筛选器：
- 时间范围（近 7 天/30 天/全部）
- 岗位类别
- 难度级别

移动端适配：
- 768px 断点：卡片从 4 列变为 2 列
- 1024px 断点：图表从并排变为堆叠

## 3. 技术选型建议

### 3.1 图表库对比

推荐：Recharts

理由：
1. 与 Ant Design 设计风格一致（简洁现代）
2. 完全用 React Hooks 编写，易于定制
3. TypeScript 支持完善
4. Bundle size 适中（90KB gzipped）
5. 社区活跃，示例丰富

安装：npm install recharts

### 3.2 状态管理

当前：纯 Zustand（轻量级项目适用）

建议：继续使用 Zustand，但规范化 store 结构

不推荐升级到 Redux Toolkit，因为：
- 项目规模适中，Zustand 足够
- 团队无 Redux 负担
- Zustand 更简洁直观

### 3.3 动画库

推荐：Framer Motion

理由：
1. 语法简洁（motion.div）
2. 内置手势支持（drag, tap, hover）
3. 与 React 生态完美集成
4. 自动布局动画（layout prop）
5. 文档优秀，示例丰富

安装：npm install framer-motion

## 4. 推荐文件结构

frontend/src/
- pages/
  - InterviewPrepPage.tsx (新增)
  - InterviewReplayPage.tsx (新增)
  - ProgressDashboardPage.tsx (新增)
  - InterviewSimulatorPage.tsx (保留)
- components/
  - interview/ (新增目录)
    - TechStackSelector.tsx
    - DifficultySelector.tsx
    - ModeSelector.tsx
    - QuestionPreview.tsx
    - ReplayTimeline.tsx
    - ChatBubble.tsx
    - ScoreCard.tsx
    - index.ts
- stores/
  - jobSearchStore.ts (现有)
  - interviewStore.ts (新增)
- services/
  - api.ts (扩展 interviewApi)
- types/
  - index.ts (扩展类型定义)

## 5. 下一步行动

### Phase 1: 类型扩展（30 分钟）
在 types/index.ts 添加新类型定义

### Phase 2: API 扩展（1 小时）
在 api.ts 扩展 interviewApi 接口

### Phase 3: 组件开发（2 小时）
抽取可复用组件，创建专用组件

### Phase 4: 页面实现（3 小时）
实现三个新页面

### Phase 5: 路由集成（30 分钟）
在 App.tsx 添加新路由

## 6. 总结

架构优势：
- 现有 Zustand 模式成熟，可直接复用
- Ant Design 组件丰富，减少重复开发
- TypeScript 类型完善，开发体验好

改进重点：
- 状态管理规范化（新建 interviewStore）
- 组件抽取（提升复用率）
- 图表集成（Recharts）
- 动画增强（Framer Motion）

预计工作量：
- 探索设计：已完成
- 实现开发：约 7-8 小时
- 测试优化：约 2-3 小时
