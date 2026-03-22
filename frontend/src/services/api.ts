import axios, { AxiosInstance, AxiosError } from 'axios'

/** 将 FastAPI / Starlette 的 detail（字符串、对象、校验错误数组）转为可读文案 */
function formatAxiosErrorMessage(error: AxiosError): string {
  if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
    return '请求超时，请确认后端已启动且网络正常；岗位爬取可能较慢，可稍后重试。'
  }
  const raw = error.response?.data
  if (raw && typeof raw === 'object' && 'detail' in raw) {
    const d = (raw as { detail: unknown }).detail
    if (typeof d === 'string') return d
    if (Array.isArray(d)) {
      try {
        return JSON.stringify(d)
      } catch {
        return '请求参数校验失败'
      }
    }
    if (d && typeof d === 'object') {
      try {
        return JSON.stringify(d)
      } catch {
        return error.message
      }
    }
  }
  return error.message
}
import type {
  ApiResponse,
  ResumeInfo,
  ResumeHistoryListItem,
  InterviewHistoryListItem,
  StudyQaGenerateResponse,
  StudyQaSessionListItem,
  StudyQaSessionDetail,
  LearningPhase,
  LearningArticleDetail,
  ResumeStreamMessage,
  InterviewSession,
  InterviewStartRequest,
  InterviewReport,
  JobSearchQuery,
  JobSearchResponse,
  SavedJobRecord,
  ResumeUploadListItem,
  UnifiedJobItem,
} from '../types'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3 分钟：AI / 爬取等较慢操作
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (axios.isCancel(error) || error.code === 'ERR_CANCELED') {
      return Promise.reject(error)
    }
    const message = formatAxiosErrorMessage(error)
    console.error('API Error:', message, error.response?.status, error.response?.data)
    return Promise.reject(new Error(message))
  }
)

// Health Check
export const checkHealth = async (): Promise<ApiResponse> => {
  const response = await api.get('/health')
  return response.data
}

// Resume APIs
export const resumeApi = {
  // Upload resume file
  upload: async (
    file: File,
    targetJobUrl?: string
  ): Promise<ApiResponse<{ id: number; filename: string; status: string }>> => {
    const formData = new FormData()
    formData.append('file', file)
    if (targetJobUrl) {
      formData.append('target_job_url', targetJobUrl)
    }
    
    const response = await api.post('/resume/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Optimize resume
  optimize: async (
    resumeId: number,
    targetJobUrl?: string
  ): Promise<ApiResponse<ResumeInfo>> => {
    const params = targetJobUrl ? `?target_job_url=${encodeURIComponent(targetJobUrl)}` : ''
    const response = await api.post(`/resume/optimize/${resumeId}${params}`)
    return response.data
  },

  optimizeStream: async (
    resumeId: number,
    onMessage: (data: ResumeStreamMessage) => void,
    targetJobUrl?: string,
    onError?: (error: Error) => void
  ): Promise<void> => {
    const params = new URLSearchParams()
    if (targetJobUrl) params.append('target_job_url', targetJobUrl)

    const url = `/api/resume/optimize/${resumeId}/stream?${params}`

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split(/\r?\n/)
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue
          try {
            const data = JSON.parse(trimmed.slice(6)) as ResumeStreamMessage
            onMessage(data)
            if (data.type === 'done' || data.type === 'error') {
              return
            }
          } catch (e) {
            console.error('Failed to parse resume SSE message:', e)
          }
        }
      }
    } catch (error) {
      console.error('Resume SSE error:', error)
      onError?.(error as Error)
    }
  },

  // Get resume details
  get: async (resumeId: number): Promise<ApiResponse<ResumeInfo>> => {
    const response = await api.get(`/resume/${resumeId}`)
    return response.data
  },

  // List resumes（全部上传记录）
  list: async (
    skip = 0,
    limit = 20
  ): Promise<
    ApiResponse<{
      resumes: ResumeUploadListItem[]
      total: number
      skip: number
      limit: number
    }>
  > => {
    const response = await api.get(`/resume?skip=${skip}&limit=${limit}`)
    return response.data
  },

  /** 已优化成功的历史记录（按更新时间倒序） */
  history: async (
    skip = 0,
    limit = 50
  ): Promise<
    ApiResponse<{
      items: ResumeHistoryListItem[]
      total: number
      skip: number
      limit: number
    }>
  > => {
    const response = await api.get(`/resume/history?skip=${skip}&limit=${limit}`)
    return response.data
  },

  // Download optimized resume
  download: async (resumeId: number, format = 'md'): Promise<string> => {
    const response = await api.get(`/resume/${resumeId}/download?format=${format}`, {
      responseType: 'text',
    })
    return response.data
  },

  // Delete resume
  delete: async (resumeId: number): Promise<ApiResponse> => {
    const response = await api.delete(`/resume/${resumeId}`)
    return response.data
  },

  /** 卡在「优化中」时恢复为「已解析」，便于重新发起 SSE 优化 */
  unlockOptimization: async (
    resumeId: number
  ): Promise<ApiResponse<{ id: number; status: string }>> => {
    const response = await api.post(`/resume/${resumeId}/unlock-optimization`)
    return response.data
  },

  /** 根据已完成优化的任务生成学习/面试准备问答（并持久化） */
  studyQa: async (
    resumeId: number
  ): Promise<ApiResponse<StudyQaGenerateResponse>> => {
    const response = await api.post(`/resume/${resumeId}/study-qa`)
    return response.data
  },

  studyQaSessions: async (
    skip = 0,
    limit = 50,
    resumeId?: number
  ): Promise<
    ApiResponse<{
      items: StudyQaSessionListItem[]
      total: number
      skip: number
      limit: number
    }>
  > => {
    let url = `/resume/study-qa-sessions?skip=${skip}&limit=${limit}`
    if (resumeId != null) url += `&resume_id=${resumeId}`
    const response = await api.get(url)
    return response.data
  },

  studyQaSessionGet: async (
    sessionId: number
  ): Promise<ApiResponse<StudyQaSessionDetail>> => {
    const response = await api.get(`/resume/study-qa-sessions/${sessionId}`)
    return response.data
  },

  studyQaSessionDelete: async (sessionId: number): Promise<ApiResponse> => {
    const response = await api.delete(`/resume/study-qa-sessions/${sessionId}`)
    return response.data
  },
}

/** 学无止境专栏 */
export const learnApi = {
  phases: async (): Promise<
    ApiResponse<{ phases: LearningPhase[] }>
  > => {
    const response = await api.get('/learn/phases')
    return response.data
  },
  article: async (articleId: number): Promise<ApiResponse<LearningArticleDetail>> => {
    const response = await api.get(`/learn/articles/${articleId}`)
    return response.data
  },
}

/** 职位搜索：传入 AbortSignal 可取消未完成的请求 */
export const jobSearchApi = {
  search: async (
    body: JobSearchQuery,
    options?: { signal?: AbortSignal }
  ): Promise<ApiResponse<JobSearchResponse>> => {
    const response = await api.post<ApiResponse<JobSearchResponse>>('/jobs/search', body, {
      signal: options?.signal,
    })
    return response.data
  },
}

/** 已保存职位（数据库持久化） */
export const jobSavedApi = {
  save: async (body: UnifiedJobItem): Promise<ApiResponse<SavedJobRecord>> => {
    const response = await api.post<ApiResponse<SavedJobRecord>>('/jobs/saved', body)
    return response.data
  },
  list: async (
    skip = 0,
    limit = 50
  ): Promise<
    ApiResponse<{
      items: SavedJobRecord[]
      total: number
      skip: number
      limit: number
    }>
  > => {
    const response = await api.get(`/jobs/saved?skip=${skip}&limit=${limit}`)
    return response.data
  },
  delete: async (jobId: number): Promise<ApiResponse<{ id: number }>> => {
    const response = await api.delete(`/jobs/saved/${jobId}`)
    return response.data
  },
  get: async (jobId: number): Promise<ApiResponse<SavedJobRecord>> => {
    const response = await api.get(`/jobs/saved/${jobId}`)
    return response.data
  },
}

/** 粘贴岗位详情 URL → 服务端爬取并写入 saved_jobs */
export const jobScrapeApi = {
  scrapeAndSave: async (
    url: string
  ): Promise<
    ApiResponse<{
      saved: SavedJobRecord
      job_snapshot: Record<string, unknown>
    }>
  > => {
    const response = await api.post('/jobs/scrape-url', { url }, { timeout: 300000 })
    return response.data
  },
  /** 上传截图 → 多模态识别并写入 saved_jobs */
  fromScreenshot: async (
    file: File
  ): Promise<
    ApiResponse<{
      saved: SavedJobRecord
      job_snapshot: Record<string, unknown>
    }>
  > => {
    const form = new FormData()
    form.append('file', file)
    // 与默认 headers 的 application/json 冲突时必须显式 multipart，否则后端收不到 file（422）
    const response = await api.post('/jobs/from-screenshot', form, {
      timeout: 300000,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

// Interview APIs
export const interviewApi = {
  // Start new interview
  start: async (
    request: InterviewStartRequest
  ): Promise<ApiResponse<InterviewSession>> => {
    const response = await api.post('/interview/start', request)
    return response.data
  },

  // Submit answer (REST API - non-streaming)
  submitAnswer: async (
    sessionId: string,
    textAnswer?: string,
    audioBase64?: string
  ): Promise<ApiResponse<InterviewSession>> => {
    const params = new URLSearchParams()
    if (textAnswer) params.append('text_answer', textAnswer)
    if (audioBase64) params.append('audio_base64', audioBase64)
    
    const response = await api.post(`/interview/${sessionId}/answer?${params}`)
    return response.data
  },

  // Submit answer with SSE streaming (using fetch for POST support)
  submitAnswerStream: async (
    sessionId: string,
    onMessage: (data: SSEMessage) => void,
    textAnswer?: string,
    audioBase64?: string,
    onError?: (error: Error) => void
  ): Promise<void> => {
    const params = new URLSearchParams()
    if (textAnswer) params.append('text_answer', textAnswer)
    if (audioBase64) params.append('audio_base64', audioBase64)
    
    const url = `/api/interview/${sessionId}/answer/stream?${params}`
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Accept': 'text/event-stream',
        },
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }
      
      const decoder = new TextDecoder()
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as SSEMessage
              onMessage(data)
              
              if (data.type === 'done' || data.type === 'error') {
                return
              }
            } catch (e) {
              console.error('Failed to parse SSE message:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('SSE error:', error)
      onError?.(error as Error)
    }
  },

  // Get interview status
  getStatus: async (sessionId: string): Promise<ApiResponse<InterviewSession>> => {
    const response = await api.get(`/interview/${sessionId}`)
    return response.data
  },

  // Get interview report
  getReport: async (sessionId: string): Promise<ApiResponse<InterviewReport>> => {
    const response = await api.get(`/interview/${sessionId}/report`)
    return response.data
  },

  // End interview early
  end: async (sessionId: string): Promise<ApiResponse> => {
    const response = await api.post(`/interview/${sessionId}/end`)
    return response.data
  },

  // List interviews
  list: async (
    skip = 0,
    limit = 20
  ): Promise<ApiResponse<{ interviews: InterviewSession[]; total: number }>> => {
    const response = await api.get(`/interview?skip=${skip}&limit=${limit}`)
    return response.data
  },

  /** 已完成的模拟面试历史（按结束时间倒序） */
  history: async (
    skip = 0,
    limit = 50
  ): Promise<
    ApiResponse<{
      items: InterviewHistoryListItem[]
      total: number
      skip: number
      limit: number
    }>
  > => {
    const response = await api.get(`/interview/history?skip=${skip}&limit=${limit}`)
    return response.data
  },

  // Create WebSocket connection
  createWebSocket: (sessionId: string): WebSocket => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return new WebSocket(`${protocol}//${host}/api/interview/ws/${sessionId}`)
  },
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

export default api
