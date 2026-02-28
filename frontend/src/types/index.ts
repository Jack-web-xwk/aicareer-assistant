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

export interface ResumeInfo {
  id: number
  original_filename: string
  file_type: string
  status: ResumeStatus
  target_job_url?: string
  target_job_title?: string
  original_text?: string
  extracted_info?: ExtractedResumeInfo
  match_analysis?: MatchAnalysis
  optimized_resume?: string
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
