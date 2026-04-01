# 面试模拟模块增强 - 基于已优化简历启动

## 📋 需求概述

原有的面试模拟功能只支持手动填写目标岗位和技术栈，范围过广，无法精准定位到具体的公司和岗位要求。本次增强实现了：

1. **从已优化简历启动面试**：通过选择已优化的简历，自动获取该简历对应的岗位信息（公司、薪资、JD 等）
2. **岗位信息持久化**：将岗位详细信息保存到 InterviewRecord，供面试官 AI 使用
3. **更精准的面试体验**：基于具体公司的岗位要求进行针对性提问

## ✅ 完成的功能

### 后端实现

#### 1. 数据模型扩展 (`backend/app/models/interview.py`)

新增字段：
- `resume_id`: 关联的简历 ID（外键）
- `company_name`: 公司名称
- `salary_text`: 薪资范围
- `location`: 工作地点
- `job_description_full`: 完整 JD
- `job_snapshot`: 岗位快照 JSON（包含技能要求、职责等）

```python
# 关联的简历 ID（可选，用于从简历优化跳转）
resume_id: Mapped[Optional[int]] = mapped_column(
    Integer,
    ForeignKey("resumes.id", ondelete="SET NULL"),
    nullable=True,
    index=True,
)

# 岗位详细信息（从简历或 saved_jobs 关联获取）
company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
salary_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
job_description_full: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
job_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

#### 2. API Schema 扩展 (`backend/app/models/schemas.py`)

`InterviewStartRequest` 增加可选参数：
```python
class InterviewStartRequest(BaseModel):
    job_role: str
    tech_stack: List[str]
    difficulty_level: str = "medium"
    resume_id: Optional[int] = None  # 从简历优化跳转时传入
```

#### 3. 面试启动 API 增强 (`backend/app/api/interview.py`)

修改 `/interview/start` API：
- 支持通过 `resume_id` 获取简历
- 从简历的 `job_snapshot` 中提取岗位信息
- 将岗位信息保存到 InterviewRecord

关键逻辑：
```python
if request.resume_id:
    resume = await db.execute(
        select(Resume).where(
            Resume.id == request.resume_id,
            Resume.user_id == user.id,
        )
    )
    if resume and resume.job_snapshot:
        job_snapshot_data = json.loads(resume.job_snapshot)
        company_name = job_snapshot_data.get("company")
        salary_text = job_snapshot_data.get("salary")
        location = job_snapshot_data.get("location")
        job_description_full = resume.job_description
        job_snapshot = resume.job_snapshot
```

#### 4. 数据库迁移脚本

创建 `backend/scripts/migrate_add_interview_job_fields.py`：
- ✅ 为 `interview_records` 表添加所有新字段
- ✅ 兼容 SQLite（try-catch 方式避免重复添加错误）

执行结果：
```
✅ 字段 resume_id 添加成功！
✅ 字段 company_name 添加成功！
✅ 字段 salary_text 添加成功！
✅ 字段 location 添加成功！
✅ 字段 job_description_full 添加成功！
✅ 字段 job_snapshot 添加成功！
```

---

### 前端实现

#### 1. 类型定义扩展 (`frontend/src/types/index.ts`)

```typescript
export interface InterviewStartRequest {
  job_role: string
  tech_stack: string[]
  difficulty_level: 'easy' | 'medium' | 'hard'
  resume_id?: number  // 可选：从简历优化跳转时传入
}
```

#### 2. 面试模拟页面增强 (`frontend/src/pages/InterviewSimulatorPage.tsx`)

**新增功能**：
- ✅ 支持从 URL 参数接收 `resumeId`
- ✅ 自动加载简历关联的岗位信息
- ✅ 展示岗位详细信息卡片（公司、薪资、地点、岗位名称）
- ✅ 自动填充技术栈（从 job_snapshot 中提取 required_skills）
- ✅ 启动面试时传递 `resume_id` 给后端

**关键代码**：

1. **URL 参数处理**：
```typescript
const [searchParams] = useSearchParams()
const resumeIdFromQuery = searchParams.get('resumeId')
```

2. **加载简历信息**：
```typescript
useEffect(() => {
  if (!resumeIdFromQuery) return
  
  const loadResumeInfo = async () => {
    const res = await resumeApi.get(parseInt(resumeIdFromQuery, 10))
    if (res.success && res.data) {
      setJobRole(data.target_job_title || data.job_snapshot?.title || '')
      setJobSnapshot(data.job_snapshot as JobSnapshot)
      setCompanyName(data.job_snapshot?.company || null)
      setSalaryText(data.job_snapshot?.salary || null)
      setLocation(data.job_snapshot?.location || null)
      
      // 自动填充技术栈
      if (data.job_snapshot?.required_skills) {
        const skills = Array.from(new Set(data.job_snapshot.required_skills))
          .slice(0, 10)
          .map(s => s.trim())
        setTechStack(skills)
      }
    }
  }
  
  loadResumeInfo()
}, [resumeIdFromQuery])
```

3. **岗位信息展示卡片**：
```tsx
{(jobSnapshot || companyName || salaryText || location) && (
  <Alert
    type="info"
    showIcon
    icon={<FieldTimeOutlined />}
    message="已加载关联简历的岗位信息"
    description={
      <Descriptions column={2} size="small" bordered>
        <Descriptions.Item label="公司名称">{companyName || '—'}</Descriptions.Item>
        <Descriptions.Item label="薪资范围">{salaryText || '—'}</Descriptions.Item>
        <Descriptions.Item label="工作地点">{location || '—'}</Descriptions.Item>
        <Descriptions.Item label="岗位名称">{jobRole || '—'}</Descriptions.Item>
      </Descriptions>
    }
    closable
  />
)}
```

4. **启动面试传递 resume_id**：
```typescript
const response = await interviewApi.start({
  job_role: jobRole,
  tech_stack: techStack,
  difficulty_level: difficulty,
  resume_id: resumeIdFromQuery ? parseInt(resumeIdFromQuery, 10) : undefined,
})
```

#### 3. 简历历史页面 (`frontend/src/pages/ResumeHistoryPage.tsx`)

已有完整的跳转逻辑：
```tsx
<Tooltip title="使用该岗位信息开始模拟面试">
  <Link to={`/interview?resumeId=${record.id}&jobUrl=${encodeURIComponent(record.target_job_url || '')}`}>
    <Button type="link" size="small" icon={<AudioOutlined />}>
      模拟面试
    </Button>
  </Link>
</Tooltip>
```

---

## 🔄 用户操作流程

### 流程一：从简历优化直接跳转

1. 用户在「简历优化」页面完成简历优化
2. 在历史结果中点击「模拟面试」按钮
3. 跳转到面试模拟页面，URL 带参数：`/interview?resumeId=123`
4. 页面自动加载岗位信息并展示
5. 用户确认信息后点击「开始面试」
6. 后端从简历获取岗位详细信息，初始化面试

### 流程二：从面试历史重新面试

1. 用户在「历史结果」→「面试模拟」Tab 查看历史面试
2. 点击某条记录的「重新面试」按钮（待实现）
3. 跳转到面试页面，带上原 `resume_id` 和 `session_id`
4. 复用原岗位信息重新开始面试

---

## 🎯 核心价值

### 用户体验提升
- ✅ **减少输入**：无需手动填写公司信息、薪资、地点等
- ✅ **精准匹配**：基于真实岗位的 JD 和要求进行面试
- ✅ **自动化**：自动填充技术栈，智能提取关键词
- ✅ **可视化**：清晰展示岗位信息，增强信心

### 技术优势
- ✅ **数据复用**：充分利用简历优化产生的 job_snapshot
- ✅ **持久化存储**：岗位信息保存到 InterviewRecord，可追溯
- ✅ **向后兼容**：resume_id 为可选参数，不影响原有手动输入模式
- ✅ **类型安全**：完整的 TypeScript 类型定义

---

## 🧪 测试要点

### 待验证场景

1. **正常流程**：
   - [ ] 从简历优化 → 面试模拟跳转
   - [ ] 岗位信息正确加载和展示
   - [ ] 技术栈自动填充正确
   - [ ] 面试启动成功，后端收到 resume_id

2. **边界情况**：
   - [ ] resume_id 无效或不存在
   - [ ] 简历无 job_snapshot 数据
   - [ ] job_snapshot 格式不正确
   - [ ] 网络请求失败

3. **兼容性**：
   - [ ] 手动输入模式仍然可用
   - [ ] 不传 resume_id 时正常工作
   - [ ] 历史面试记录不受影响

---

## 📝 后续优化建议

### 短期优化
1. **面试历史重新面试**：在面试历史记录中添加「重新面试」按钮，复用原岗位信息
2. **岗位信息编辑**：允许用户在自动填充基础上微调
3. **加载状态优化**：添加骨架屏和加载动画

### 长期优化
1. **AI 智能推荐**：根据简历内容推荐最匹配的面试难度
2. **多岗位对比**：支持同时选择多个 offer 进行对比面试
3. **面试报告增强**：在面试报告中显示岗位信息，便于回顾

---

## 🔗 相关文件清单

### 后端文件
- `backend/app/models/interview.py` - InterviewRecord 模型
- `backend/app/models/schemas.py` - InterviewStartRequest schema
- `backend/app/api/interview.py` - /interview/start API
- `backend/scripts/migrate_add_interview_job_fields.py` - 数据库迁移脚本

### 前端文件
- `frontend/src/types/index.ts` - InterviewStartRequest 类型定义
- `frontend/src/pages/InterviewSimulatorPage.tsx` - 面试模拟主页面
- `frontend/src/pages/ResumeHistoryPage.tsx` - 简历历史页面（已有跳转按钮）

---

## ✨ 完成状态

- ✅ 后端数据模型扩展
- ✅ 后端 API 增强
- ✅ 数据库迁移
- ✅ 前端类型定义
- ✅ 前端页面增强
- ✅ URL 参数传递
- ✅ 岗位信息展示
- ✅ 技术栈自动填充
- ⏳ 端到端测试验证

---

**创建时间**: 2026-04-01  
**作者**: AI Assistant  
**版本**: v1.0
