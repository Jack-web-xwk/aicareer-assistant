import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  ApiResponse,
  ResumeInfo,
  InterviewSession,
  InterviewStartRequest,
  InterviewReport,
} from '../types'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 60000, // 60 seconds for AI operations
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = (error.response?.data as { detail?: string })?.detail || error.message
    console.error('API Error:', message)
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

  // Get resume details
  get: async (resumeId: number): Promise<ApiResponse<ResumeInfo>> => {
    const response = await api.get(`/resume/${resumeId}`)
    return response.data
  },

  // List resumes
  list: async (
    skip = 0,
    limit = 20
  ): Promise<ApiResponse<{ resumes: ResumeInfo[]; total: number }>> => {
    const response = await api.get(`/resume?skip=${skip}&limit=${limit}`)
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

  // Submit answer (REST API)
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

  // Create WebSocket connection
  createWebSocket: (sessionId: string): WebSocket => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return new WebSocket(`${protocol}//${host}/api/interview/ws/${sessionId}`)
  },
}

export default api
