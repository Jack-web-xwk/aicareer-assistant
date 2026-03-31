"""
Pydantic Schemas - 请求/响应模型

定义 API 的请求和响应数据结构。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, EmailStr, ConfigDict


# ==================== Assessment Dimension Enums ====================

class AssessmentDimension(str, Enum):
    """面试评估维度"""
    TECHNICAL_DEPTH = "technical_depth"  # 技术深度
    TECHNICAL_BREADTH = "technical_breadth"  # 技术广度
    COMMUNICATION = "communication"  # 沟通表达
    LOGIC = "logic"  # 逻辑思维
    PROBLEM_SOLVING = "problem_solving"  # 问题解决
    
    @property
    def weight(self) -> float:
        """获取维度权重"""
        weights = {
            "technical_depth": 0.25,      # 25%
            "technical_breadth": 0.20,    # 20%
            "communication": 0.20,        # 20%
            "logic": 0.20,                # 20%
            "problem_solving": 0.15,      # 15%
        }
        return weights.get(self.value, 0.0)
    
    @property
    def display_name(self) -> str:
        """获取维度显示名称"""
        names = {
            "technical_depth": "技术深度",
            "technical_breadth": "技术广度",
            "communication": "沟通表达",
            "logic": "逻辑思维",
            "problem_solving": "问题解决",
        }
        return names.get(self.value, self.value)


# ==================== Common Schemas ====================

class SuccessResponse(BaseModel):
    """通用成功响应"""
    success: bool = True
    message: str = "Operation successful"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """通用错误响应"""
    success: bool = False
    error: Dict[str, Any] = Field(
        default_factory=lambda: {
            "code": "UNKNOWN_ERROR",
            "message": "An error occurred",
            "details": {},
        }
    )


# ==================== User Schemas ====================

class UserCreate(BaseModel):
    """用户创建请求"""
    email: EmailStr
    username: Optional[str] = None


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    email: str
    username: Optional[str]
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Resume Schemas ====================

class ResumeUploadRequest(BaseModel):
    """简历上传请求（元数据）"""
    target_job_url: Optional[str] = Field(
        None,
        description="目标岗位链接（Boss直聘）",
    )


class ResumeOptimizeRequest(BaseModel):
    """简历优化请求"""
    resume_id: int = Field(..., description="简历 ID")
    target_job_url: str = Field(..., description="目标岗位链接")


class ExtractedResumeInfo(BaseModel):
    """提取的简历信息"""
    name: Optional[str] = None
    contact: Optional[Dict[str, str]] = None
    education: Optional[List[Dict[str, Any]]] = None
    work_experience: Optional[List[Dict[str, Any]]] = None
    projects: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    summary: Optional[str] = None


class JobRequirements(BaseModel):
    """岗位需求信息（爬取/解析结果，用于优化与历史展示）"""
    title: str
    company: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    company_scale: Optional[str] = None
    financing_stage: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list, description="岗位职责要点")
    qualifications: List[str] = Field(
        default_factory=list,
        description="任职要求（与职责区分；图中「任职要求」段落拆条）",
    )
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    tech_stack_tags: List[str] = Field(
        default_factory=list,
        description="页面技能/技术标签（如 Boss 职位旁的标签云）",
    )
    benefits: List[str] = Field(default_factory=list, description="福利标签，如五险一金、下午茶等")
    experience_years: Optional[str] = None
    education_requirement: Optional[str] = None
    work_address: Optional[str] = Field(None, description="详细办公地址（若图中有）")
    work_schedule: Optional[str] = Field(None, description="工作时间、双休等")
    recruiter_name: Optional[str] = None
    recruiter_title: Optional[str] = None


class MatchAnalysis(BaseModel):
    """匹配分析结果"""
    match_score: float = Field(..., ge=0, le=100)
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    strengths: List[str] = []
    areas_to_improve: List[str] = []
    suggestions: List[str] = []


class StudyQaItem(BaseModel):
    """简历优化任务衍生的学习 / 面试准备问答项"""

    topic: str = Field(..., description="主题归类，如「岗位匹配」「技能补缺」")
    question: str = Field(..., description="问题")
    answer_hint: str = Field(
        ...,
        description="答题要点或思路提示（非标准答案，仅供自学）",
    )


class StudyQaResponseData(BaseModel):
    """POST /resume/{id}/study-qa 返回的 data 结构"""

    items: List[StudyQaItem] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    """简历信息响应"""
    id: int
    original_filename: str
    file_type: str
    status: str
    target_job_title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OptimizedResumeResponse(BaseModel):
    """优化后的简历响应"""
    id: int
    original_filename: str
    status: str
    extracted_info: Optional[ExtractedResumeInfo] = None
    job_requirements: Optional[JobRequirements] = None
    match_analysis: Optional[MatchAnalysis] = None
    optimized_resume: Optional[str] = None  # Markdown format
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Interview Schemas ====================

class InterviewStartRequest(BaseModel):
    """开始面试请求"""
    job_role: str = Field(..., description="目标岗位")
    tech_stack: List[str] = Field(
        ...,
        description="技术栈范围",
    )
    difficulty_level: str = Field(
        default="medium",
        description="难度级别",
    )


class InterviewMessageRequest(BaseModel):
    """面试消息请求（用于 REST API）"""
    session_id: str = Field(..., description="面试会话 ID")
    message: Optional[str] = Field(None, description="用户文本消息")
    audio_base64: Optional[str] = Field(None, description="用户语音（Base64 编码）")


class InterviewMessage(BaseModel):
    """面试对话消息"""
    role: str = Field(..., description="消息角色", pattern="^(user|assistant)$")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audio_url: Optional[str] = None


class InterviewResponse(BaseModel):
    """面试响应"""
    session_id: str
    job_role: str
    status: str
    current_question: Optional[str] = None
    question_number: int = 0
    total_questions: int = 5
    audio_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class QuestionScore(BaseModel):
    """单题评分"""
    question_number: int
    question: str
    answer_summary: str
    score: float = Field(..., ge=0, le=100)
    feedback: str


class InterviewReportResponse(BaseModel):
    """面试评估报告响应"""
    session_id: str
    job_role: str
    tech_stack: List[str]
    duration_minutes: Optional[float] = None
    total_score: float = Field(..., ge=0, le=100)
    question_scores: List[QuestionScore] = []
    dimension_scores: Optional[List["DimensionScore"]] = None  # 多维度评分
    strengths: List[str] = []
    weaknesses: List[str] = []
    suggestions: List[str] = []
    detailed_report: Optional[str] = None  # Markdown format
    realtime_feedback_log: Optional[List["RealTimeFeedback"]] = None  # 实时反馈历史
    learning_plan: Optional["LearningSuggestion"] = None  # 个性化学习计划
    completed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Multi-Dimensional Assessment Schemas ====================

class DimensionScore(BaseModel):
    """维度评分"""
    dimension_id: AssessmentDimension = Field(..., description="评估维度 ID")
    score: float = Field(..., ge=0, le=100, description="维度得分 (0-100)")
    feedback: str = Field(..., description="维度详细反馈")
    key_points: List[str] = Field(default_factory=list, description="关键评分要点")
    weight: float = Field(default=0.0, description="权重")
    
    @property
    def weighted_score(self) -> float:
        """计算加权分数"""
        return self.score * self.weight


class RealTimeFeedback(BaseModel):
    """实时反馈"""
    session_id: str = Field(..., description="面试会话 ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="反馈时间")
    dimension_scores: List[DimensionScore] = Field(default_factory=list, description="当前维度评分")
    overall_feedback: str = Field(..., description="整体反馈")
    suggestions: List[str] = Field(default_factory=list, description="即时建议")
    response_time_ms: Optional[int] = Field(None, ge=0, description="响应时间 (毫秒)")


class LearningSuggestion(BaseModel):
    """学习建议"""
    dimension: AssessmentDimension = Field(..., description="薄弱维度")
    weakness: str = Field(..., description="具体薄弱点描述")
    learning_resources: List[Dict[str, Any]] = Field(default_factory=list, description="学习资源推荐")
    action_items: List[str] = Field(default_factory=list, description="行动计划")
    priority: str = Field(default="medium", description="优先级 (high/medium/low)")
    estimated_hours: Optional[int] = Field(None, ge=0, description="预计学习时长 (小时)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dimension": "technical_depth",
                "weakness": "对并发编程原理理解不够深入",
                "learning_resources": [
                    {
                        "title": "Java 并发编程实战",
                        "type": "book",
                        "url": "https://example.com/book"
                    },
                    {
                        "title": "Coursera - 并行编程课程",
                        "type": "course",
                        "url": "https://coursera.org/learn/parallel-programming"
                    }
                ],
                "action_items": [
                    "阅读《Java 并发编程实战》第 1-5 章",
                    "完成并发编程练习题",
                    "实现一个线程池 Demo"
                ],
                "priority": "high",
                "estimated_hours": 20
            }
        }
    )


# ==================== WebSocket Message Schemas ====================

class WSMessage(BaseModel):
    """WebSocket 消息基类"""
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(default_factory=dict)


class WSAudioMessage(BaseModel):
    """WebSocket 音频消息"""
    type: str = "audio"
    audio_base64: str = Field(..., description="Base64 编码的音频数据")


class WSTextMessage(BaseModel):
    """WebSocket 文本消息"""
    type: str = "text"
    content: str = Field(..., description="文本内容")


class WSControlMessage(BaseModel):
    """WebSocket 控制消息"""
    type: str = "control"
    action: str = Field(..., description="控制动作", pattern="^(start|end|pause|resume)$")


# ==================== Learning Schemas ====================

class LearningArticleListItem(BaseModel):
    """文章列表项（不含正文）"""
    id: int
    phase_id: int
    title: str
    sort_order: int
    external_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningPhaseOut(BaseModel):
    """阶段（含文章列表）"""
    id: int
    title: str
    subtitle: str
    sort_order: int
    articles: List[LearningArticleListItem] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningArticleDetail(BaseModel):
    """文章详情（含正文）"""
    id: int
    phase_id: int
    title: str
    sort_order: int
    content_md: str
    external_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Question Bank Schemas ====================

class QuestionBankBase(BaseModel):
    """题库基础 Schema"""
    category: str = Field(..., description="分类名称，如'后端开发'、'前端开发'")
    tech_stack: Optional[List[str]] = Field(None, description="技术栈列表")
    difficulty: str = Field(default="medium", description="难度级别 (easy/medium/hard)")
    question: str = Field(..., description="问题描述")
    expected_points: Optional[List[str]] = Field(None, description="期望回答要点")
    follow_up_questions: Optional[List[str]] = Field(None, description="追问问题列表")


class QuestionBankCreate(QuestionBankBase):
    """创建题目请求"""
    pass


class QuestionBankUpdate(BaseModel):
    """更新题目请求"""
    category: Optional[str] = Field(None, description="分类名称")
    tech_stack: Optional[List[str]] = Field(None, description="技术栈列表")
    difficulty: Optional[str] = Field(None, description="难度级别")
    question: Optional[str] = Field(None, description="问题描述")
    expected_points: Optional[List[str]] = Field(None, description="期望回答要点")
    follow_up_questions: Optional[List[str]] = Field(None, description="追问问题列表")
    is_active: Optional[bool] = Field(None, description="是否启用")


class QuestionBankResponse(QuestionBankBase):
    """题目响应"""
    id: int
    usage_count: int = 0
    avg_score: Optional[float] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionBankSearchRequest(BaseModel):
    """搜索题目请求"""
    keyword: Optional[str] = Field(None, description="关键词")
    category: Optional[str] = Field(None, description="分类")
    difficulty: Optional[str] = Field(None, description="难度级别")
    tech_stack: Optional[List[str]] = Field(None, description="技术栈")
    offset: int = Field(default=0, ge=0, description="偏移量")
    limit: int = Field(default=20, ge=1, le=100, description="数量限制")


class QuestionBankStatistics(BaseModel):
    """题库统计响应"""
    total_count: int = Field(..., description="总题目数")
    category_stats: Dict[str, int] = Field(default_factory=dict, description="按分类统计")
    difficulty_stats: Dict[str, int] = Field(default_factory=dict, description="按难度统计")
    avg_usage: float = Field(..., description="平均使用次数")
    avg_score: Optional[float] = Field(None, description="平均得分")
    top_questions: List[Dict[str, Any]] = Field(default_factory=list, description="热门题目")


class QuestionBankBatchImportRequest(BaseModel):
    """批量导入请求"""
    questions: List[Dict[str, Any]] = Field(..., description="题目数据列表")
    skip_duplicates: bool = Field(default=True, description="是否跳过重复题目")


class QuestionBankBatchImportResponse(BaseModel):
    """批量导入响应"""
    imported: int = Field(..., description="成功导入数量")
    skipped: int = Field(..., description="跳过数量")
    failed: int = Field(..., description="失败数量")
    total: int = Field(..., description="总数")

