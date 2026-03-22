"""
Pydantic Schemas - 请求/响应模型

定义 API 的请求和响应数据结构。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, EmailStr


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
    
    class Config:
        from_attributes = True


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
    
    class Config:
        from_attributes = True


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
    
    class Config:
        from_attributes = True


# ==================== Interview Schemas ====================

class InterviewStartRequest(BaseModel):
    """开始面试请求"""
    job_role: str = Field(..., description="目标岗位", example="Python后端工程师")
    tech_stack: List[str] = Field(
        ...,
        description="技术栈范围",
        example=["Python", "FastAPI", "PostgreSQL", "Redis"],
    )
    difficulty_level: str = Field(
        default="medium",
        description="难度级别",
        pattern="^(easy|medium|hard)$",
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
    
    class Config:
        from_attributes = True


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
    strengths: List[str] = []
    weaknesses: List[str] = []
    suggestions: List[str] = []
    detailed_report: Optional[str] = None  # Markdown format
    completed_at: datetime
    
    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


class LearningPhaseOut(BaseModel):
    """阶段（含文章列表）"""
    id: int
    title: str
    subtitle: str
    sort_order: int
    articles: List[LearningArticleListItem] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True
