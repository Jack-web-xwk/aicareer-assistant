// API Response Types

export interface ApiResponse<T = unknown> {
  success: boolean
  message: string
  data?: T
}

export interface ErrorResponse {
  success: false
  error: {
    code: string
    message: string
    details?: Record<string, unknown>
  }
}

// Resume Types

/** 与后端 JobRequirements + source_url 一致，用于历史/详情展示 */
export interface JobSnapshot {
  title?: string
  company?: string | null
  salary?: string | null
  location?: string | null
  industry?: string | null
  company_scale?: string | null
  financing_stage?: string | null
  responsibilities?: string[]
  qualifications?: string[]
  required_skills?: string[]
  preferred_skills?: string[]
  tech_stack_tags?: string[]
  benefits?: string[]
  experience_years?: string | null
  education_requirement?: string | null
  work_address?: string | null
  work_schedule?: string | null
  recruiter_name?: string | null
  recruiter_title?: string | null
  source_url?: string
  scrape_error?: string
}

export interface ResumeInfo {
  id: number
  original_filename: string
  file_type: string
  status: ResumeStatus
  target_job_url?: string
  target_job_title?: string
  job_description?: string | null
  job_snapshot?: JobSnapshot | null
  original_text?: string
  extracted_info?: ExtractedResumeInfo
  match_analysis?: MatchAnalysis
  optimized_resume?: string
  error_message?: string | null
  created_at: string
  updated_at: string
}

export type ResumeStatus = 
  | 'uploaded'
  | 'parsing'
  | 'parsed'
  | 'optimizing'
  | 'optimized'
  | 'failed'

export interface ExtractedResumeInfo {
  name?: string
  contact?: {
    email?: string
    phone?: string
    location?: string
  }
  summary?: string
  education?: Array<{
    school: string
    degree: string
    major: string
    start_date?: string
    end_date?: string
    gpa?: string
    highlights?: string[]
  }>
  work_experience?: Array<{
    company: string
    title: string
    start_date?: string
    end_date?: string
    responsibilities?: string[]
    achievements?: string[]
  }>
  projects?: Array<{
    name: string
    role?: string
    description?: string
    technologies?: string[]
    achievements?: string[]
  }>
  skills?: {
    programming_languages?: string[]
    frameworks?: string[]
    tools?: string[]
    soft_skills?: string[]
  }
  certifications?: string[]
  languages?: string[]
}

export interface MatchAnalysis {
  match_score: number
  matched_skills: string[]
  missing_skills: string[]
  strengths: string[]
  areas_to_improve: string[]
  suggestions: string[]
}

/** POST /resume/{id}/study-qa 返回的单条学习/面试准备问答 */
export interface StudyQaItem {
  topic: string
  question: string
  answer_hint: string
}

/** POST /resume/{id}/study-qa 成功后的 data（含持久化字段） */
export interface StudyQaGenerateResponse {
  session_id: number
  resume_id: number
  items: StudyQaItem[]
  item_count: number
  created_at: string
}

/** GET /resume/study-qa-sessions 列表项 */
export interface StudyQaSessionListItem {
  id: number
  resume_id: number
  original_filename: string
  target_job_title?: string | null
  item_count: number
  preview?: string | null
  created_at: string
}

/** GET /resume/study-qa-sessions/{id} 详情 */
export interface StudyQaSessionDetail {
  id: number
  resume_id: number
  original_filename: string
  file_type: string
  target_job_title?: string | null
  target_job_url?: string | null
  status: string
  items: StudyQaItem[]
  item_count: number
  created_at: string
}

// Learn (学无止境) Types

export interface LearningArticleListItem {
  id: number
  phase_id: number
  title: string
  sort_order: number
  external_url?: string | null
  created_at: string
}

export interface LearningPhase {
  id: number
  title: string
  subtitle: string
  sort_order: number
  articles: LearningArticleListItem[]
  created_at: string
}

export interface LearningArticleDetail {
  id: number
  phase_id: number
  title: string
  sort_order: number
  content_md: string
  external_url?: string | null
  created_at: string
  updated_at: string
}

/** GET /resume/history 列表项（无完整正文） */
export interface ResumeHistoryListItem {
  id: number
  original_filename: string
  file_type: string
  status: ResumeStatus
  target_job_title?: string | null
  target_job_url?: string | null
  match_score?: number | null
  preview?: string | null
  job_snapshot?: JobSnapshot | null
  error_message?: string | null
  created_at: string
  updated_at: string
}

/** GET /interview/history 列表项（无完整报告正文） */
export interface InterviewHistoryListItem {
  session_id: string
  job_role: string
  tech_stack: string[]
  total_score: number | null
  duration_minutes: number | null
  preview?: string | null
  started_at: string
  ended_at: string | null
}

/** LangGraph 图中节点 id，与后端 StateGraph 节点名一致 */
export type ResumeOptimizerGraphNode =
  | 'extract_resume_info'
  | 'analyze_job_requirements'
  | 'match_content'
  | 'generate_optimized_resume'

/** 单个 LangGraph 节点完成后推送的详情（SSE node_complete） */
export interface ResumeNodeOutputPayload {
  data?: Record<string, unknown>
  thinking?: string | null
  rawPreview?: string | null
}

export interface ResumeStreamMessage {
  type: 'start' | 'progress' | 'token' | 'done' | 'error' | 'node_complete'
  message?: string
  step?: ResumeOptimizerGraphNode
  /** 与 step 相同，显式标注 LangGraph 节点 */
  node?: ResumeOptimizerGraphNode
  delta?: string
  optimized_resume?: string
  extracted_info?: ExtractedResumeInfo
  match_analysis?: MatchAnalysis
  /** node_complete：该节点结构化输出 */
  data?: Record<string, unknown>
  /** node_complete：模型分析思路 / reasoning_notes / 厂商推理字段 */
  thinking?: string | null
  /** node_complete：模型原始输出片段（便于核对） */
  raw_preview?: string | null
}

// Interview Types

export interface InterviewSession {
  session_id: string
  job_role: string
  tech_stack: string[]
  status: InterviewStatus
  current_question?: string
  question_number: number
  total_questions: number
  audio_base64?: string
  is_finished: boolean
}

export type InterviewStatus = 'in_progress' | 'completed' | 'cancelled'

export interface InterviewStartRequest {
  job_role: string
  tech_stack: string[]
  difficulty_level: 'easy' | 'medium' | 'hard'
}

export interface InterviewAnswerRequest {
  text_answer?: string
  audio_base64?: string
}

export interface InterviewReport {
  session_id: string
  job_role: string
  tech_stack: string[]
  total_score: number
  strengths: string[]
  weaknesses: string[]
  suggestions: string[]
  detailed_report?: string
  duration_minutes?: number
  completed_at: string
  conversation_history?: InterviewMessage[]
}

export interface InterviewMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  audio_url?: string
}

// WebSocket Message Types

export interface WSMessage {
  type: 'init' | 'response' | 'error'
  session_id?: string
  job_role?: string
  current_question?: string
  question_number?: number
  audio_base64?: string
  transcript?: string
  is_finished?: boolean
  report?: InterviewReport
  message?: string
}

export interface WSAudioMessage {
  type: 'audio'
  audio_base64: string
}

export interface WSTextMessage {
  type: 'text'
  content: string
}

export interface WSEndMessage {
  type: 'end'
}

// SSE Message Types

export interface SSEMessage {
  type: 'start' | 'processing' | 'response' | 'done' | 'error'
  message?: string
  session_id?: string
  is_finished?: boolean
  current_question?: string
  question_number?: number
  total_questions?: number
  audio_base64?: string
  transcript?: string
  report?: InterviewReport
}

// Job search (multi-source aggregation)

export type JobSource = 'boss' | 'zhaopin' | 'yupao' | 'link' | 'screenshot'

export type JobMatchMode = 'fuzzy' | 'exact'

export type JobSortBy = 'published_at' | 'salary'

export type JobSortOrder = 'desc' | 'asc'

export interface UnifiedJobItem {
  title: string
  company_name: string
  salary_text: string
  location: string
  published_at?: string | null
  experience_text: string
  education_text: string
  source: JobSource
  detail_url: string
  raw_snippet?: string | null
}

export interface JobSearchQuery {
  keyword: string
  company_keyword: string
  match_mode: JobMatchMode
  city?: string | null
  salary_min?: number | null
  salary_max?: number | null
  experience?: string | null
  sources: JobSource[]
  sort_by: JobSortBy
  sort_order: JobSortOrder
  page: number
  page_size: number
}

export interface JobSearchResponse {
  items: UnifiedJobItem[]
  total: number
  page: number
  page_size: number
  sources_used: string[]
  cached: boolean
  warning?: string | null
}

/** 数据库中保存的职位（POST /jobs/saved 与 GET /jobs/saved） */
export type SavedJobRecord = UnifiedJobItem & {
  id: number
  created_at: string
  updated_at: string
}

/** GET /resume 上传记录列表项 */
export interface ResumeUploadListItem {
  id: number
  original_filename: string
  file_type: string
  status: ResumeStatus
  target_job_title?: string | null
  target_job_url?: string | null
  error_message?: string | null
  created_at: string
  updated_at: string
}

// ============================================================================
// Pod-C: Interview Prep & UX Types
// ============================================================================

/** 面试准备模式 */
export type PrepMode = 'practice' | 'mock' | 'challenge'

/** 能力维度类型（5 个评估维度） */
export type DimensionType = 
  | 'technical_skill'      // 技术能力
  | 'communication'        // 沟通能力
  | 'problem_solving'      // 问题解决
  | 'project_experience'   // 项目经验
  | 'cultural_fit'         // 文化匹配

/** 难度级别 */
export type DifficultyLevel = 'easy' | 'medium' | 'hard'

/** 题目信息 */
export interface InterviewQuestion {
  id: number
  content: string
  dimension: DimensionType
  difficulty: DifficultyLevel
  tags: string[]
  expected_duration_seconds: number
  tips?: string
}

/** 准备答案提交 */
export interface PrepAnswerRequest {
  session_id: string
  question_id: number
  text_answer: string
  audio_base64?: string
  duration_seconds: number
}

/** 准备答案响应 */
export interface PrepAnswerResponse {
  success: boolean
  feedback: string
  score: number
  suggestions: string[]
}

/** 回放会话信息 */
export interface ReplaySession {
  session_id: string
  job_role: string
  tech_stack: string[]
  started_at: string
  ended_at: string
  total_score: number
  dimension_scores: Record<DimensionType, number>
  conversation_history: ReplayMessage[]
  comparison_data?: ComparisonView
}

/** 回放中的消息 */
export interface ReplayMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  audio_url?: string
  dimension?: DimensionType
  score?: number
  feedback?: string
}

/** A/B 答案对比视图 */
export interface ComparisonView {
  answer_a: {
    content: string
    audio_url?: string
    duration_seconds: number
    score: number
    feedback: string
  }
  answer_b: {
    content: string
    audio_url?: string
    duration_seconds: number
    score: number
    feedback: string
  }
  comparison_summary: string
  improvement_suggestions: string[]
}

/** 进度统计数据 */
export interface ProgressStats {
  user_id: string
  timeframe: 'week' | 'month' | 'quarter' | 'year'
  total_interviews: number
  average_score: number
  best_dimension: DimensionType
  weakest_dimension: DimensionType
  dimension_averages: Record<DimensionType, number>
  activity_days: number
  streak_days: number
}

/** 趋势数据点 */
export interface TrendDataPoint {
  date: string
  score: number
  interview_count: number
  dimension_scores?: Partial<Record<DimensionType, number>>
}

/** 热力图数据 */
export interface HeatmapData {
  month: string  // YYYY-MM
  days: Array<{
    date: string  // YYYY-MM-DD
    count: number
    intensity: number  // 0-1
  }>
  total_practice_days: number
  max_intensity: number
}

/** 反馈时间轴项 */
export interface FeedbackTimelineItem {
  id: string
  timestamp: string
  type: 'question' | 'answer' | 'feedback' | 'milestone'
  content: string
  dimension?: DimensionType
  score?: number
  icon?: string
}

/** 维度评分卡数据 */
export interface DimensionScoreCardData {
  dimension: DimensionType
  score: number
  max_score: number
  feedback: string
  trend: 'up' | 'down' | 'stable'
  previous_score?: number
  strengths: string[]
  areas_to_improve: string[]
}

/** API 请求参数类型 */
export interface PrepQuestionsParams {
  mode: PrepMode
  tech_stack: string[]
  difficulty?: DifficultyLevel
  dimensions?: DimensionType[]
  limit?: number
}

export interface ReplayHistoryParams {
  session_id?: string
  skip?: number
  limit?: number
}

export interface ProgressStatsParams {
  user_id: string
  timeframe?: 'week' | 'month' | 'quarter' | 'year'
}
