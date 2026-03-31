# UX 设计文档 - Pod C: 面试体验增强

## 1. 信息架构

### 站点地图

```
/ (首页)
├── /jobs (职位搜索)
├── /target-jobs (目标岗位)
├── /jobs/saved (我的职位)
├── /resume (简历优化)
├── /resume/history (历史结果)
├── /interview (面试模拟)
│   ├── /interview/prep (准备模式) [新增]
│   └── /interview/replay/:id (面试回放) [新增]
├── /learn (学无止境)
└── /progress (进度 Dashboard) [新增]
```

### 导航菜单更新

建议在"面试模拟"下添加子菜单或下拉选项：
- 面试准备
- 面试回放  
- 进度 Dashboard（也可作为独立主菜单）

---

## 2. 组件设计

### 2.1 InterviewPrepPage (准备模式)

**页面功能:**
- 展示用户统计数据
- 选择岗位和技术栈
- 选择面试模式（练习/模拟/挑战）
- 预览题库（3-5 题）
- 设置时间限制

**State 定义:**
```typescript
interface PrepPageState {
  jobRole: string
  techStack: string[]
  difficulty: 'easy' | 'medium' | 'hard'
  mode: 'practice' | 'mock' | 'challenge'
  timeLimit?: number
  questionPreview?: QuestionItem[]
  stats?: UserInterviewStats
  loading: boolean
}
```

**子组件:**
- StatsCard - 统计卡片
- JobRoleSelector - 岗位选择器
- TechStackSelector - 技术栈选择器（复用现有）
- DifficultySelector - 难度选择器（复用现有）
- ModeSelector - 模式选择卡片
- QuestionPreview - 题库预览列表
- TimeLimitSlider - 时间限制滑块

**API 需求:**
```
GET /api/interview/question-preview?job_role=xxx&tech_stack[]=xxx&limit=5
GET /api/user/interview/stats
POST /api/interview/start (扩展示支持 mode 和 time_limit)
```

---

### 2.2 InterviewReplayPage (面试回放)

**页面功能:**
- 时间轴拖拽定位
- 对话气泡展示
- 显示评分和反馈
- 支持重新回答对比

**Props:**
```typescript
interface ReplayPageProps {
  sessionId: string  // 路由参数
}
```

**State 定义:**
```typescript
interface ReplayPageState {
  replayData?: InterviewReplayData
  currentPosition: number  // 当前问题索引
  isPlaying: boolean
  showFeedback: boolean
  comparingAnswer: boolean
  originalAnswer?: string
  newAnswer?: string
  loading: boolean
}
```

**Timeline 交互设计:**
- 拖拽滑块快速跳转到某个问题
- 点击问题节点直接跳转
- 已回答问题显示实心圆，未回答显示空心圆
- Hover 显示该题得分和简要反馈

**子组件:**
- ReplayTimeline - 时间轴组件
- ChatBubble - 对话气泡（区分 AI/用户）
- FeedbackCard - 反馈卡片
- AnswerComparison - 回答对比组件
- PlaybackControls - 播放控制按钮

**API 需求:**
```
GET /api/interview/{session_id}/replay
POST /api/interview/{session_id}/re-answer (可选)
```

---

### 2.3 ProgressDashboardPage (进度看板)

**页面功能:**
- 统计卡片展示
- 分数趋势图
- 能力雷达图
- 技术栈热力图
- 最近面试记录

**State 定义:**
```typescript
interface DashboardPageState {
  filters: DashboardFilters
  stats?: DashboardStats
  trendData?: ScoreTrendData[]
  radarData?: AbilityRadarData[]
  heatmapData?: TechStackHeatmapData[]
  recentInterviews?: InterviewHistoryItem[]
  loading: boolean
}

interface DashboardFilters {
  timeRange: '7d' | '30d' | '90d' | 'all'
  jobRole?: string
  difficulty?: 'easy' | 'medium' | 'hard'
}
```

**图表配置:**

1. 分数趋势图 (Recharts ComposedChart)
   - X 轴：日期
   - 左 Y 轴：分数 (0-100)
   - 右 Y 轴：面试次数
   - 折线：平均分趋势
   - 柱状：面试次数

2. 能力雷达图 (Recharts RadarChart)
   - 五维度：技术/沟通/逻辑/表达/潜力
   - 满分 100 分

3. 技术栈热力图 (Recharts BarChart)
   - 水平条形图
   - X 轴：掌握度 (0-100)
   - Y 轴：技术栈名称
   - 颜色深浅表示熟练度

**筛选器状态管理:**
使用 Zustand store 持久化筛选条件

**API 需求:**
```
GET /api/user/progress/dashboard?time_range=30d&job_role=xxx&difficulty=xxx
```

---

## 3. API 需求详情

### 3.1 GET /api/interview/question-preview
获取题库预览（用于准备模式）

请求参数:
- job_role: string
- tech_stack: string[] (可多个)
- limit: number (默认 5)

响应数据结构:
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "question": "Python 装饰器的原理是什么？",
        "category": "technical",
        "difficulty": "medium",
        "tags": ["Python", "装饰器"]
      }
    ],
    "total_available": 50
  }
}
```

### 3.2 GET /api/interview/{session_id}/replay
获取面试回放完整数据

响应数据结构:
```json
{
  "success": true,
  "data": {
    "session_info": {
      "session_id": "uuid",
      "job_role": "Python 后端工程师",
      "tech_stack": ["Python", "FastAPI"],
      "started_at": "2024-03-27T10:00:00Z",
      "duration_minutes": 25
    },
    "questions": [
      {
        "question_number": 1,
        "question": "请介绍一下 Python 的装饰器",
        "user_answer": "装饰器是一个函数...",
        "score": 80,
        "feedback": "概念清晰，但缺少代码示例",
        "strengths": ["理解准确"],
        "weaknesses": ["缺少实例"],
        "timestamp": "2024-03-27T10:02:00Z",
        "duration_seconds": 120
      }
    ],
    "total_score": 85,
    "report": {...}
  }
}
```

### 3.3 GET /api/user/progress/dashboard
获取进度 Dashboard 聚合数据

请求参数:
- time_range: '7d' | '30d' | '90d' | 'all'
- job_role: string (可选)
- difficulty: string (可选)

响应数据结构:
```json
{
  "success": true,
  "data": {
    "stats": {
      "total_interviews": 12,
      "avg_score": 78.5,
      "highest_score": 92,
      "streak_days": 5,
      "percentile": 85
    },
    "trend": [...],
    "abilities": [...],
    "tech_stacks": [...],
    "recent_interviews": [...]
  }
}
```

### 3.4 GET /api/user/interview/stats
获取用户面试统计摘要

响应数据结构:
```json
{
  "success": true,
  "data": {
    "total_interviews": 12,
    "avg_score": 78.5,
    "completed_today": 1,
    "streak_days": 5
  }
}
```

---

## 4. 响应式设计

### 断点定义
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### 布局变化

准备模式:
- Mobile: 统计卡片单列，表单垂直堆叠
- Tablet: 统计卡片 2 列，表单双列
- Desktop: 统计卡片 4 列，表单单列居中

回放页面:
- Mobile: 时间轴简化，对话气泡全宽
- Tablet: 时间轴显示编号，带 avatar
- Desktop: 左右分栏，左侧对话右侧反馈

进度 Dashboard:
- Mobile: 统计卡片 2x2，图表垂直堆叠
- Tablet: 统计卡片 4 列，图表 2x2 网格
- Desktop: 统计卡片 4 列，图表上 2 下 1

### 触摸优化
- 时间轴支持拖拽
- Swipe 手势切换题目
- Tap 显示/隐藏反馈
- Long press 复制内容

---

## 5. 无障碍访问

### 键盘导航
- Tab 顺序：筛选器 -> 主要内容 -> 操作按钮
- 快捷键：
  - Space: 播放/暂停
  - Left/Right: 上一题/下一题
  - Home/End: 第一题/最后一题
  - F: 切换反馈

### 屏幕阅读器
- ARIA 标签标注控件
- role="status" 实时通知
- alt 文本描述图表

---

## 6. 设计规范

### 颜色
- Primary: #6366f1
- Secondary: #8b5cf6
- Success: #10b981 (80-100 分)
- Warning: #f59e0b (60-79 分)
- Error: #ef4444 (0-59 分)

### 字体大小
- xs: 0.75rem (辅助文字)
- sm: 0.875rem (次要文字)
- base: 1rem (正文)
- lg: 1.125rem (小标题)
- xl: 1.25rem (中标题)
- 2xl: 1.5rem (大标题)

### 间距
- 1: 0.25rem (4px)
- 2: 0.5rem (8px)
- 3: 0.75rem (12px)
- 4: 1rem (16px)
- 6: 1.5rem (24px)
- 8: 2rem (32px)

---

## 7. 性能优化

### 代码分割
使用 React.lazy 懒加载页面组件

### 数据预取
使用 React Query 预取题库数据

### Loading 状态
- 骨架屏：卡片和列表
- Spinner: 按钮和小区域
- Progress bar: 长时间操作

### 错误处理
- 空状态设计
- 网络错误提示
- 重试机制

---

## 8. 总结

本文档描述了三个新页面的详细设计：

1. **准备模式**: 提供面试前准备和模式选择
2. **回放页面**: 支持时间轴拖拽和回答对比
3. **进度 Dashboard**: 可视化学习进度和能力维度

需要后端提供 4 个新 API 接口支持。

下一步将根据此设计实现具体组件。
