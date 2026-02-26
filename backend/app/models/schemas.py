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
    """岗位需求信息"""
    title: str
    company: Optional[str] = None
    responsibilities: List[str] = []
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    experience_years: Optional[str] = None
    education_requirement: Optional[str] = None


class MatchAnalysis(BaseModel):
    """匹配分析结果"""
    match_score: float = Field(..., ge=0, le=100)
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    strengths: List[str] = []
    areas_to_improve: List[str] = []
    suggestions: List[str] = []


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
