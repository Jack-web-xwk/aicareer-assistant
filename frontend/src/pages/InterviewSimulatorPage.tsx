import { useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Card,
  Row,
  Col,
  Typography,
  Input,
  Button,
  Select,
  Space,
  message,
  Progress,
  Tag,
  List,
  Avatar,
  Divider,
  Spin,
  Descriptions,
  Alert,
} from 'antd'
import {
  AudioOutlined,
  UserOutlined,
  RobotOutlined,
  SendOutlined,
  StopOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  FieldTimeOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { interviewApi, resumeApi, jobSavedApi } from '../services/api'
import type { InterviewSession, InterviewReport, WSMessage, SSEMessage, ResumeUploadListItem, SavedJobRecord } from '../types'

const { Title, Paragraph, Text } = Typography
const { TextArea } = Input

// Common tech stacks
const TECH_STACK_OPTIONS = [
  { label: 'Python', value: 'Python' },
  { label: 'FastAPI', value: 'FastAPI' },
  { label: 'Django', value: 'Django' },
  { label: 'Flask', value: 'Flask' },
  { label: 'JavaScript', value: 'JavaScript' },
  { label: 'TypeScript', value: 'TypeScript' },
  { label: 'React', value: 'React' },
  { label: 'Vue', value: 'Vue' },
  { label: 'Node.js', value: 'Node.js' },
  { label: 'Go', value: 'Go' },
  { label: 'Java', value: 'Java' },
  { label: 'Spring', value: 'Spring' },
  { label: 'MySQL', value: 'MySQL' },
  { label: 'PostgreSQL', value: 'PostgreSQL' },
  { label: 'Redis', value: 'Redis' },
  { label: 'MongoDB', value: 'MongoDB' },
  { label: 'Docker', value: 'Docker' },
  { label: 'Kubernetes', value: 'Kubernetes' },
  { label: 'AWS', value: 'AWS' },
  { label: 'Git', value: 'Git' },
]

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  audioBase64?: string
}

interface JobSnapshot {
  title?: string
  company?: string
  company_name?: string
  salary?: string
  salary_text?: string
  location?: string
  required_skills?: string[]
  [key: string]: unknown
}

function InterviewSimulatorPage() {
  // URL 参数
  const [searchParams] = useSearchParams()
  const resumeIdFromQuery = searchParams.get('resumeId')
  
  // State
  const [stage, setStage] = useState<'setup' | 'interview' | 'report'>('setup')
  const [jobRole, setJobRole] = useState('')
  const [techStack, setTechStack] = useState<string[]>([])
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium')
  const [loading, setLoading] = useState(false)
  
  // 岗位详细信息（从简历关联获取）
  const [jobSnapshot, setJobSnapshot] = useState<JobSnapshot | null>(null)
  const [companyName, setCompanyName] = useState<string | null>(null)
  const [companyBusiness, setCompanyBusiness] = useState<string>('')
  const [salaryText, setSalaryText] = useState<string | null>(null)
  const [location, setLocation] = useState<string | null>(null)
  const [jobDescriptionOverride, setJobDescriptionOverride] = useState<string>('')
  const [jdSource, setJdSource] = useState<'resume_snapshot' | 'saved_job'>('resume_snapshot')
  const [optimizedResumes, setOptimizedResumes] = useState<ResumeUploadListItem[]>([])
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [savedJobs, setSavedJobs] = useState<SavedJobRecord[]>([])
  const [selectedSavedJobId, setSelectedSavedJobId] = useState<number | null>(null)
  
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const [report, setReport] = useState<InterviewReport | null>(null)
  const [currentPhase, setCurrentPhase] = useState<'intro' | 'technical_core' | 'deep_dive' | 'wrap_up'>('intro')
  const [minRounds, setMinRounds] = useState(4)
  const [isRecording, setIsRecording] = useState(false)
  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const [audioPlaying, setAudioPlaying] = useState(false)
  
  // WebSocket
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const recordedChunksRef = useRef<Blob[]>([])
  const recordingTimerRef = useRef<number | null>(null)
  const currentAudioRef = useRef<HTMLAudioElement | null>(null)

  // Auto scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (recordingTimerRef.current) {
        window.clearInterval(recordingTimerRef.current)
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (currentAudioRef.current) {
        currentAudioRef.current.pause()
        currentAudioRef.current = null
      }
    }
  }, [])

  const blobToBase64 = useCallback((blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const result = reader.result
        if (typeof result !== 'string') {
          reject(new Error('录音读取失败'))
          return
        }
        const base64 = result.includes(',') ? result.split(',')[1] : result
        resolve(base64)
      }
      reader.onerror = () => reject(new Error('录音读取失败'))
      reader.readAsDataURL(blob)
    })
  }, [])

  const playAudioFromBase64 = useCallback((audioBase64?: string) => {
    if (!audioBase64) return

    try {
      const source = audioBase64.startsWith('data:')
        ? audioBase64
        : `data:audio/mp3;base64,${audioBase64}`

      if (currentAudioRef.current) {
        currentAudioRef.current.pause()
      }

      const audio = new Audio(source)
      currentAudioRef.current = audio
      setAudioPlaying(true)

      const finishPlayback = () => {
        setAudioPlaying(false)
      }

      audio.onended = finishPlayback
      audio.onerror = finishPlayback

      void audio.play().catch(() => {
        setAudioPlaying(false)
      })
    } catch {
      setAudioPlaying(false)
    }
  }, [])

  const attachAudioToLastAssistantMessage = useCallback((audioBase64?: string) => {
    if (!audioBase64) return
    setMessages((prev) => {
      const list = [...prev]
      for (let i = list.length - 1; i >= 0; i -= 1) {
        if (list[i].role === 'assistant') {
          list[i] = { ...list[i], audioBase64 }
          break
        }
      }
      return list
    })
  }, [])

  // 从 URL 参数加载简历信息
  useEffect(() => {
    if (!resumeIdFromQuery) return
    
    const loadResumeInfo = async () => {
      try {
        const res = await resumeApi.get(parseInt(resumeIdFromQuery, 10))
        if (res.success && res.data) {
          const data = res.data
          
          // 设置岗位信息
          setJobRole(data.target_job_title || data.job_snapshot?.title || '')
          if (data.job_snapshot) {
            setJobSnapshot(data.job_snapshot as JobSnapshot)
          }
          const snapshot = data.job_snapshot as any
          setCompanyName(snapshot?.company || snapshot?.company_name || null)
          setCompanyBusiness(snapshot?.industry || snapshot?.company_business || '')
          setSalaryText(snapshot?.salary || snapshot?.salary_text || null)
          setLocation(snapshot?.location || null)
          setJobDescriptionOverride(data.job_description || '')
          setSelectedResumeId(data.id)
          
          // 自动填充技术栈（从 job_snapshot 中提取）
          if (data.job_snapshot?.required_skills && Array.isArray(data.job_snapshot.required_skills)) {
            // 提取关键技术栈（去重，限制数量）
            const skills = Array.from(new Set(data.job_snapshot.required_skills))
              .slice(0, 10)
              .map(s => s.trim())
              .filter(s => s.length > 0)
            setTechStack(skills)
          }
          
          message.success('已加载简历关联的岗位信息')
        }
      } catch (e) {
        console.error('加载简历信息失败:', e)
        message.warning('加载简历信息失败，请手动填写岗位信息')
      }
    }
    
    loadResumeInfo()
  }, [resumeIdFromQuery])

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const [resumeListRes, savedJobsRes] = await Promise.all([
          resumeApi.list(0, 100),
          jobSavedApi.list(0, 100),
        ])
        if (resumeListRes.success && resumeListRes.data?.items) {
          setOptimizedResumes(resumeListRes.data.items.filter((r) => r.status === 'optimized'))
        }
        if (savedJobsRes.success && savedJobsRes.data?.items) {
          setSavedJobs(savedJobsRes.data.items)
        }
      } catch {
        // ignore non-critical loading errors
      }
    }
    void loadOptions()
  }, [])

  const loadResumeContext = useCallback(async (resumeId: number) => {
    try {
      const res = await resumeApi.get(resumeId)
      if (!res.success || !res.data) return
      const data = res.data
      setSelectedResumeId(data.id)
      setJobRole(data.target_job_title || data.job_snapshot?.title || '')
      if (data.job_snapshot) {
        setJobSnapshot(data.job_snapshot as JobSnapshot)
      }
      const snapshot = data.job_snapshot as any
      setCompanyName(snapshot?.company || snapshot?.company_name || null)
      setCompanyBusiness(snapshot?.industry || snapshot?.company_business || '')
      setSalaryText(snapshot?.salary || snapshot?.salary_text || null)
      setLocation(snapshot?.location || null)
      setJobDescriptionOverride(data.job_description || '')
      if (data.job_snapshot?.required_skills && Array.isArray(data.job_snapshot.required_skills)) {
        const skills = Array.from(new Set(data.job_snapshot.required_skills))
          .slice(0, 10)
          .map(s => s.trim())
          .filter(s => s.length > 0)
        setTechStack(skills)
      }
    } catch {
      message.warning('加载简历上下文失败')
    }
  }, [])

  // Start interview
  const handleStartInterview = async () => {
    if (!jobRole) {
      message.error('请输入目标岗位')
      return
    }
    if (techStack.length === 0) {
      message.error('请选择至少一个技术栈')
      return
    }
  
    setLoading(true)
    try {
      const response = await interviewApi.start({
        job_role: jobRole,
        tech_stack: techStack,
        difficulty_level: difficulty,
        resume_id: resumeIdFromQuery ? parseInt(resumeIdFromQuery, 10) : undefined,
        context_resume_id: selectedResumeId || undefined,
        saved_job_id: jdSource === 'saved_job' ? (selectedSavedJobId || undefined) : undefined,
        company_name: companyName || undefined,
        company_business: companyBusiness || undefined,
        job_description_override: jobDescriptionOverride || undefined,
      })
  
      if (response.success && response.data) {
        setSession(response.data)
        setMessages([
          {
            role: 'assistant',
            content: response.data.current_question || '面试开始！',
            timestamp: new Date(),
            audioBase64: response.data.audio_base64,
          },
        ])
        setStage('interview')
        message.success('面试开始！')
        playAudioFromBase64(response.data.audio_base64)
  
        // Setup WebSocket for real-time communication
        const ws = interviewApi.createWebSocket(response.data.session_id)
        wsRef.current = ws
  
        ws.onmessage = (event) => {
          const data: WSMessage = JSON.parse(event.data)

          if (data.type === 'round_progress') {
            const phase = data.data?.phase
            if (phase) {
              setCurrentPhase(phase)
            }
            const min = data.data?.min_rounds
            if (typeof min === 'number') {
              setMinRounds(min)
            }
          } else if (data.type === 'transcript_final') {
            const transcriptText = data.data?.text || ''
            if (transcriptText) {
              setMessages((prev) => {
                const next = [...prev]
                for (let i = next.length - 1; i >= 0; i -= 1) {
                  if (next[i].role === 'user' && next[i].content.startsWith('🎤 语音回答')) {
                    next[i] = {
                      ...next[i],
                      content: `🎤 语音回答（转写）：${transcriptText}`,
                    }
                    break
                  }
                }
                return next
              })
            }
          } else if (data.type === 'interviewer_reply') {
            const text = data.data?.text
            if (text) {
              setMessages((prev) => {
                const newMessages = [...prev]
                const lastIndex = newMessages.length - 1
                if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                  newMessages[lastIndex] = {
                    ...newMessages[lastIndex],
                    content: text,
                  }
                } else {
                  newMessages.push({ role: 'assistant', content: text, timestamp: new Date() })
                }
                return newMessages
              })
            }
          } else if (data.type === 'interviewer_audio') {
            const audioB64 = data.data?.audio_base64
            attachAudioToLastAssistantMessage(audioB64)
            playAudioFromBase64(audioB64)
          } else if (data.type === 'session_completed') {
            // keep compatibility response for report details
          } else if (data.type === 'response') {
            // Update the placeholder message instead of adding a new one
            setMessages((prev) => {
              const newMessages = [...prev]
              const lastIndex = newMessages.length - 1
              if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                newMessages[lastIndex] = {
                  ...newMessages[lastIndex],
                  content: data.current_question || '面试结束，正在生成报告...',
                }
              }
              return newMessages
            })
            attachAudioToLastAssistantMessage(data.audio_base64)
            playAudioFromBase64(data.audio_base64)
  
            if (data.is_finished && data.report) {
              setReport(data.report)
              setStage('report')
            }
          } else if (data.type === 'error') {
            message.error(data.message || '发生错误')
            // Remove the placeholder message
            setMessages((prev) => prev.slice(0, -1))
          }
        }
  
        ws.onerror = () => {
          message.error('WebSocket 连接失败，将使用 REST API')
        }
      }
    } catch (error) {
      message.error(`开始面试失败：${(error as Error).message}`)
    } finally {
      setLoading(false)
    }
  }

  const sendAudioAnswer = useCallback(async (audioBase64: string, durationSeconds: number) => {
    if (!session) return

    const userMessage = `🎤 语音回答（${durationSeconds}秒）`

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: userMessage,
        timestamp: new Date(),
      },
    ])

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: '正在思考中...',
        timestamp: new Date(),
      },
    ])

    setLoading(true)

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'audio', audio_base64: audioBase64 }))
      setLoading(false)
    } else {
      try {
        await interviewApi.submitAnswerStream(
          session.session_id,
          (data: SSEMessage) => {
            if (data.type === 'round_progress') {
              const phase = data.data?.phase
              if (phase) setCurrentPhase(phase)
              const min = data.data?.min_rounds
              if (typeof min === 'number') setMinRounds(min)
            } else if (data.type === 'transcript_final') {
              const transcriptText = data.data?.text || ''
              if (transcriptText) {
                setMessages((prev) => {
                  const next = [...prev]
                  for (let i = next.length - 1; i >= 0; i -= 1) {
                    if (next[i].role === 'user' && next[i].content.startsWith('🎤 语音回答')) {
                      next[i] = {
                        ...next[i],
                        content: `🎤 语音回答（转写）：${transcriptText}`,
                      }
                      break
                    }
                  }
                  return next
                })
              }
            } else if (data.type === 'interviewer_reply') {
              const text = data.data?.text
              if (text) {
                setMessages((prev) => {
                  const newMessages = [...prev]
                  const lastIndex = newMessages.length - 1
                  if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                    newMessages[lastIndex] = {
                      ...newMessages[lastIndex],
                      content: text,
                    }
                  }
                  return newMessages
                })
              }
            } else if (data.type === 'interviewer_audio') {
              playAudioFromBase64(data.data?.audio_base64)
            } else if (data.type === 'start') {
              // Update the placeholder message
              setMessages((prev) => {
                const newMessages = [...prev]
                const lastIndex = newMessages.length - 1
                if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                  newMessages[lastIndex] = {
                    ...newMessages[lastIndex],
                    content: data.message || '正在处理...',
                  }
                }
                return newMessages
              })
            } else if (data.type === 'processing') {
              // Update with processing message
              setMessages((prev) => {
                const newMessages = [...prev]
                const lastIndex = newMessages.length - 1
                if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                  newMessages[lastIndex] = {
                    ...newMessages[lastIndex],
                    content: data.message || '分析回答中...',
                  }
                }
                return newMessages
              })
            } else if (data.type === 'response') {
              // Update session and messages
              if (data.current_question) {
                setMessages((prev) => {
                  const newMessages = [...prev]
                  const lastIndex = newMessages.length - 1
                  if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                    newMessages[lastIndex] = {
                      ...newMessages[lastIndex],
                      content: data.current_question || '',
                    }
                  }
                  return newMessages
                })
              playAudioFromBase64(data.audio_base64)
              }

              setSession({
                session_id: data.session_id || session.session_id,
                job_role: session.job_role,
                tech_stack: session.tech_stack,
                status: data.is_finished ? 'completed' : 'in_progress',
                current_question: data.current_question,
                question_number: data.question_number || 0,
                total_questions: data.total_questions || 5,
                is_finished: data.is_finished || false,
              })

              if (data.is_finished && data.report) {
                setReport(data.report)
                setStage('report')
              }
            } else if (data.type === 'error') {
              message.error(data.message || '发生错误')
              // Remove the placeholder message
              setMessages((prev) => prev.slice(0, -1))
            }
          },
          undefined,
          audioBase64,
          (error: Error) => {
            message.error(`发送失败: ${error.message}`)
            setMessages((prev) => prev.slice(0, -1))
            setLoading(false)
          }
        )
      } catch (error) {
        message.error(`发送失败: ${(error as Error).message}`)
        setMessages((prev) => prev.slice(0, -1))
      } finally {
        setLoading(false)
      }
    }
  }, [attachAudioToLastAssistantMessage, playAudioFromBase64, session])

  // Send text answer
  const handleSendAnswer = async () => {
    if (!inputText.trim() || !session) return

    const userMessage = inputText.trim()
    setInputText('')

    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: userMessage,
        timestamp: new Date(),
      },
    ])

    // Add a placeholder for AI response
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: '正在思考中...',
        timestamp: new Date(),
      },
    ])

    setLoading(true)

    // Try WebSocket first
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text', content: userMessage }))
      setLoading(false)
    } else {
      // Use SSE streaming
      try {
        await interviewApi.submitAnswerStream(
          session.session_id,
          (data: SSEMessage) => {
            if (data.type === 'round_progress') {
              const phase = data.data?.phase
              if (phase) setCurrentPhase(phase)
              const min = data.data?.min_rounds
              if (typeof min === 'number') setMinRounds(min)
            } else if (data.type === 'transcript_final') {
              // 文本回答场景一般无转写，这里保留兼容
            } else if (data.type === 'interviewer_reply') {
              const text = data.data?.text
              if (text) {
                setMessages((prev) => {
                  const newMessages = [...prev]
                  const lastIndex = newMessages.length - 1
                  if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                    newMessages[lastIndex] = {
                      ...newMessages[lastIndex],
                      content: text,
                    }
                  }
                  return newMessages
                })
              }
            } else if (data.type === 'interviewer_audio') {
              attachAudioToLastAssistantMessage(data.data?.audio_base64)
              playAudioFromBase64(data.data?.audio_base64)
            } else if (data.type === 'start') {
              // Update the placeholder message
              setMessages((prev) => {
                const newMessages = [...prev]
                const lastIndex = newMessages.length - 1
                if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                  newMessages[lastIndex] = {
                    ...newMessages[lastIndex],
                    content: data.message || '正在处理...',
                  }
                }
                return newMessages
              })
            } else if (data.type === 'processing') {
              // Update with processing message
              setMessages((prev) => {
                const newMessages = [...prev]
                const lastIndex = newMessages.length - 1
                if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                  newMessages[lastIndex] = {
                    ...newMessages[lastIndex],
                    content: data.message || '分析回答中...',
                  }
                }
                return newMessages
              })
            } else if (data.type === 'response') {
              // Update session and messages
              if (data.current_question) {
                setMessages((prev) => {
                  const newMessages = [...prev]
                  const lastIndex = newMessages.length - 1
                  if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                    newMessages[lastIndex] = {
                      ...newMessages[lastIndex],
                      content: data.current_question || '',
                    }
                  }
                  return newMessages
                })
              }
              attachAudioToLastAssistantMessage(data.audio_base64)
              playAudioFromBase64(data.audio_base64)

              setSession({
                session_id: data.session_id || session.session_id,
                job_role: session.job_role,
                tech_stack: session.tech_stack,
                status: data.is_finished ? 'completed' : 'in_progress',
                current_question: data.current_question,
                question_number: data.question_number || 0,
                total_questions: data.total_questions || 5,
                is_finished: data.is_finished || false,
              })

              if (data.is_finished && data.report) {
                setReport(data.report)
                setStage('report')
              }
            } else if (data.type === 'error') {
              message.error(data.message || '发生错误')
              // Remove the placeholder message
              setMessages((prev) => prev.slice(0, -1))
            }
          },
          userMessage,
          undefined,
          (error: Error) => {
            message.error(`发送失败: ${error.message}`)
            // Remove the placeholder message
            setMessages((prev) => prev.slice(0, -1))
            setLoading(false)
          }
        )
      } catch (error) {
        message.error(`发送失败: ${(error as Error).message}`)
        // Remove the placeholder message
        setMessages((prev) => prev.slice(0, -1))
      } finally {
        setLoading(false)
      }
    }
  }

  const handleStartRecording = async () => {
    if (loading) return
    if (!('MediaRecorder' in window) || !navigator.mediaDevices?.getUserMedia) {
      message.error('当前浏览器不支持录音')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
      recordedChunksRef.current = []

      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingSeconds(0)
      recordingTimerRef.current = window.setInterval(() => {
        setRecordingSeconds((prev) => prev + 1)
      }, 1000)
    } catch {
      message.error('无法访问麦克风，请检查浏览器权限')
    }
  }

  const handleStopRecording = async () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') return

    const recorder = mediaRecorderRef.current
    const durationSeconds = recordingSeconds

    if (recordingTimerRef.current) {
      window.clearInterval(recordingTimerRef.current)
      recordingTimerRef.current = null
    }
    setIsRecording(false)

    recorder.onstop = async () => {
      try {
        const audioBlob = new Blob(recordedChunksRef.current, { type: 'audio/webm' })
        const base64 = await blobToBase64(audioBlob)
        await sendAudioAnswer(base64, durationSeconds)
      } catch (error) {
        message.error(`语音发送失败: ${(error as Error).message}`)
      } finally {
        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach((track) => track.stop())
          mediaStreamRef.current = null
        }
      }
    }

    recorder.stop()
  }

  // End interview early
  const handleEndInterview = async () => {
    if (!session) return

    setLoading(true)
    try {
      await interviewApi.end(session.session_id)
      
      const reportResponse = await interviewApi.getReport(session.session_id)
      if (reportResponse.success && reportResponse.data) {
        setReport(reportResponse.data)
        setStage('report')
      }
      
      message.success('面试已结束')
    } catch (error) {
      message.error(`结束面试失败: ${(error as Error).message}`)
    } finally {
      setLoading(false)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }

  // Reset
  const handleReset = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    setStage('setup')
    setJobRole('')
    setTechStack([])
    setDifficulty('medium')
    setSession(null)
    setMessages([])
    setReport(null)
  }

  // Get score color
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10b981'
    if (score >= 60) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div className="fade-in">
      <Title level={2} style={{ color: 'var(--color-text-primary)', marginBottom: '24px' }}>
        <AudioOutlined style={{ marginRight: '12px', color: '#8b5cf6' }} />
        语音技术面试模拟
      </Title>

      {/* Setup Stage */}
      {stage === 'setup' && (
        <Card
          style={{
            maxWidth: '800px',
            margin: '0 auto',
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid var(--color-border)',
          }}
        >
          <Title level={4} style={{ color: 'var(--color-text-primary)' }}>
            配置面试参数
          </Title>
      
          {/* 岗位详细信息展示（从简历关联获取） */}
          {(jobSnapshot || companyName || salaryText || location) && (
            <Alert
              type="info"
              showIcon
              icon={<FieldTimeOutlined />}
              message="已加载关联简历的岗位信息"
              description={
                <Descriptions column={2} size="small" bordered>
                  <Descriptions.Item label="公司名称">
                    {companyName || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="薪资范围">
                    {salaryText || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="工作地点">
                    {location || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="岗位名称">
                    {jobRole || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="公司业务">
                    {companyBusiness || '—'}
                  </Descriptions.Item>
                </Descriptions>
              }
              style={{ marginBottom: '24px' }}
              closable
              onClose={() => {
                setJobSnapshot(null)
                setCompanyName(null)
                setSalaryText(null)
                setLocation(null)
              }}
            />
          )}
      
          <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
              目标岗位
            </Text>
            <Input
              size="large"
              placeholder="例如：Python 后端工程师"
              value={jobRole}
              onChange={(e) => setJobRole(e.target.value)}
            />
          </div>
      
          <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
              选择已优化简历（可选）
            </Text>
            <Select
              size="large"
              style={{ width: '100%' }}
              placeholder="选择一份 optimized 简历作为上下文"
              value={selectedResumeId || undefined}
              onChange={(v) => {
                const next = Number(v)
                setSelectedResumeId(Number.isNaN(next) ? null : next)
                if (!Number.isNaN(next)) {
                  void loadResumeContext(next)
                }
              }}
              allowClear
              options={optimizedResumes.map((r) => ({
                label: `${r.original_filename} (#${r.id})`,
                value: r.id,
              }))}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
              技术栈范围
            </Text>
            <Select
              mode="multiple"
              size="large"
              style={{ width: '100%' }}
              placeholder="选择技术栈"
              value={techStack}
              onChange={setTechStack}
              options={TECH_STACK_OPTIONS}
            />
          </div>
      
          <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
              JD 来源（可选）
            </Text>
            <Select
              size="large"
              style={{ width: '100%' }}
              value={jdSource}
              onChange={(v) => setJdSource(v as 'resume_snapshot' | 'saved_job')}
              options={[
                { label: '简历快照（默认）', value: 'resume_snapshot' },
                { label: '我的岗位', value: 'saved_job' },
              ]}
            />
          </div>

          {jdSource === 'saved_job' && (
            <div style={{ marginBottom: '24px' }}>
              <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
                选择我的岗位
              </Text>
              <Select
                size="large"
                style={{ width: '100%' }}
                placeholder="从我的岗位中选择"
                value={selectedSavedJobId || undefined}
                onChange={(v) => {
                  const id = Number(v)
                  setSelectedSavedJobId(Number.isNaN(id) ? null : id)
                  const selected = savedJobs.find((s) => s.id === id)
                  if (selected) {
                    setCompanyName(selected.company_name || null)
                    const pseudoJd = `岗位：${selected.title}\n经验要求：${selected.experience_text}\n学历要求：${selected.education_text}`
                    setJobDescriptionOverride(pseudoJd)
                  }
                }}
                allowClear
                options={savedJobs.map((j) => ({
                  label: `${j.title} - ${j.company_name}`,
                  value: j.id,
                }))}
              />
            </div>
          )}

          <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
              公司名称（可选）
            </Text>
            <Input
              size="large"
              placeholder="例如：某某科技有限公司"
              value={companyName || ''}
              onChange={(e) => setCompanyName(e.target.value || null)}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
              公司业务（可选）
            </Text>
            <Input
              size="large"
              placeholder="例如：企业级SaaS、跨境电商、AI应用"
              value={companyBusiness}
              onChange={(e) => setCompanyBusiness(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <Space style={{ width: '100%', justifyContent: 'space-between', marginBottom: '8px' }}>
              <Text style={{ color: 'var(--color-text-secondary)' }}>
                岗位JD（可选）
              </Text>
              <Button
                size="small"
                onClick={() => {
                  if (selectedResumeId) {
                    void loadResumeContext(selectedResumeId)
                  }
                }}
                disabled={!selectedResumeId}
              >
                恢复简历默认JD
              </Button>
            </Space>
            <TextArea
              placeholder="可编辑岗位JD；优先级高于自动来源"
              value={jobDescriptionOverride}
              onChange={(e) => setJobDescriptionOverride(e.target.value)}
              autoSize={{ minRows: 5, maxRows: 10 }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
              难度级别
            </Text>
            <Select
              size="large"
              style={{ width: '100%' }}
              value={difficulty}
              onChange={setDifficulty}
              options={[
                { label: '初级 - 基础概念和常见用法', value: 'easy' },
                { label: '中级 - 原理理解和实际应用', value: 'medium' },
                { label: '高级 - 深入原理和架构设计', value: 'hard' },
              ]}
            />
          </div>
      
          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            onClick={handleStartInterview}
            loading={loading}
            style={{ width: '100%' }}
          >
            开始面试
          </Button>
        </Card>
      )}

      {/* Interview Stage */}
      {stage === 'interview' && session && (
        <Row gutter={[24, 24]}>
          {/* Chat Area */}
          <Col xs={24} lg={16}>
            <Card
              title={
                <Space>
                  <span>面试进行中</span>
                  <Tag color="processing">
                    问题 {session.question_number} / {session.total_questions}
                  </Tag>
                </Space>
              }
              extra={
                <Button
                  danger
                  icon={<StopOutlined />}
                  onClick={handleEndInterview}
                  loading={loading}
                >
                  结束面试
                </Button>
              }
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid var(--color-border)',
              }}
              bodyStyle={{ padding: 0 }}
            >
              {/* Messages */}
              <div
                style={{
                  height: '400px',
                  overflowY: 'auto',
                  padding: '16px',
                }}
              >
                <List
                  itemLayout="horizontal"
                  dataSource={messages}
                  renderItem={(msg) => {
                    const isLoading = msg.role === 'assistant' && 
                      (msg.content === '正在思考中...' || 
                       msg.content === '正在处理...' || 
                       msg.content === '分析回答中...' ||
                       msg.content.includes('正在'))
                      
                    return (
                      <List.Item
                        style={{
                          borderBottom: 'none',
                          padding: '12px 0',
                        }}
                      >
                        <List.Item.Meta
                          avatar={
                            <Avatar
                              icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                              style={{
                                backgroundColor: msg.role === 'user' ? '#6366f1' : '#8b5cf6',
                              }}
                            />
                          }
                          title={
                            <Text style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>
                              {msg.role === 'user' ? '你' : 'AI 面试官'} ·{' '}
                              {msg.timestamp.toLocaleTimeString()}
                            </Text>
                          }
                          description={
                            <div style={{ color: 'var(--color-text-primary)', marginTop: '4px' }}>
                              {isLoading ? (
                                <Space>
                                  <Spin indicator={<LoadingOutlined style={{ fontSize: 16 }} spin />} />
                                  <span>{msg.content}</span>
                                </Space>
                              ) : (
                                <>
                                  <div>{msg.content}</div>
                                  {msg.role === 'assistant' && msg.audioBase64 && (
                                    <Button
                                      size="small"
                                      type="link"
                                      icon={<PlayCircleOutlined />}
                                      onClick={() => playAudioFromBase64(msg.audioBase64)}
                                      style={{ paddingLeft: 0, marginTop: 4 }}
                                    >
                                      重播语音
                                    </Button>
                                  )}
                                </>
                              )}
                            </div>
                          }
                        />
                      </List.Item>
                    )
                  }}
                />
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div
                style={{
                  padding: '16px',
                  borderTop: '1px solid var(--color-border)',
                }}
              >
                <Space.Compact style={{ width: '100%' }}>
                  <TextArea
                    placeholder="输入你的回答..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onPressEnter={(e) => {
                      if (!e.shiftKey) {
                        e.preventDefault()
                        handleSendAnswer()
                      }
                    }}
                    autoSize={{ minRows: 1, maxRows: 4 }}
                    style={{ flex: 1 }}
                  />
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    onClick={handleSendAnswer}
                    loading={loading}
                    disabled={isRecording}
                  >
                    发送
                  </Button>
                  <Button
                    icon={<AudioOutlined />}
                    danger={isRecording}
                    onClick={isRecording ? handleStopRecording : handleStartRecording}
                    disabled={loading}
                  >
                    {isRecording ? `停止录音 (${recordingSeconds}s)` : '语音回答'}
                  </Button>
                </Space.Compact>
                <Text
                  type="secondary"
                  style={{ fontSize: '12px', display: 'block', marginTop: '8px' }}
                >
                  提示: 按 Enter 发送，Shift + Enter 换行；点击“语音回答”开始录音，停止后自动发送
                </Text>
                {audioPlaying && (
                  <Text type="secondary" style={{ fontSize: '12px', display: 'block', marginTop: '4px' }}>
                    AI 语音播放中...
                  </Text>
                )}
              </div>
            </Card>
          </Col>

          {/* Info Sidebar */}
          <Col xs={24} lg={8}>
            <Card
              title="面试信息"
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div style={{ marginBottom: '16px' }}>
                <Text style={{ color: 'var(--color-text-muted)' }}>目标岗位</Text>
                <div style={{ color: 'var(--color-text-primary)', fontSize: '16px' }}>
                  {session.job_role}
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <Text style={{ color: 'var(--color-text-muted)' }}>技术栈</Text>
                <div style={{ marginTop: '8px' }}>
                  {session.tech_stack.map((tech, index) => (
                    <Tag key={index} color="blue" style={{ marginBottom: '4px' }}>
                      {tech}
                    </Tag>
                  ))}
                </div>
              </div>

              <div>
                <Text style={{ color: 'var(--color-text-muted)' }}>进度</Text>
                <Progress
                  percent={(session.question_number / session.total_questions) * 100}
                  strokeColor="#6366f1"
                  format={() =>
                    `${session.question_number}/${session.total_questions}`
                  }
                />
                <Text style={{ color: 'var(--color-text-muted)', display: 'block', marginTop: 8 }}>
                  当前阶段：{currentPhase}
                </Text>
                <Text style={{ color: 'var(--color-text-muted)', display: 'block' }}>
                  最少轮次：{minRounds}（达到后才会自动结束）
                </Text>
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* Report Stage */}
      {stage === 'report' && report && (
        <Row gutter={[24, 24]}>
          {/* Score Overview */}
          <Col xs={24} md={8}>
            <Card
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid var(--color-border)',
                textAlign: 'center',
              }}
            >
              <Progress
                type="circle"
                percent={report.total_score}
                size={150}
                strokeColor={getScoreColor(report.total_score)}
                format={(percent) => (
                  <span
                    style={{
                      color: getScoreColor(percent || 0),
                      fontSize: '32px',
                      fontWeight: 'bold',
                    }}
                  >
                    {percent}
                  </span>
                )}
              />
              <Title level={4} style={{ color: 'var(--color-text-primary)', marginTop: '16px' }}>
                面试总分
              </Title>
              {report.duration_minutes && (
                <Text style={{ color: 'var(--color-text-muted)' }}>
                  用时: {Math.round(report.duration_minutes)} 分钟
                </Text>
              )}
            </Card>
          </Col>

          {/* Strengths & Weaknesses */}
          <Col xs={24} md={16}>
            <Card
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid var(--color-border)',
              }}
            >
              <Row gutter={[24, 24]}>
                <Col xs={24} md={12}>
                  <Title level={5} style={{ color: '#10b981' }}>
                    <CheckCircleOutlined /> 优势
                  </Title>
                  <List
                    size="small"
                    dataSource={report.strengths}
                    renderItem={(item) => (
                      <List.Item style={{ borderColor: 'var(--color-border)' }}>
                        <Text style={{ color: 'var(--color-text-secondary)' }}>
                          ✓ {item}
                        </Text>
                      </List.Item>
                    )}
                  />
                </Col>
                <Col xs={24} md={12}>
                  <Title level={5} style={{ color: '#ef4444' }}>
                    <CloseCircleOutlined /> 待改进
                  </Title>
                  <List
                    size="small"
                    dataSource={report.weaknesses}
                    renderItem={(item) => (
                      <List.Item style={{ borderColor: 'var(--color-border)' }}>
                        <Text style={{ color: 'var(--color-text-secondary)' }}>
                          ✗ {item}
                        </Text>
                      </List.Item>
                    )}
                  />
                </Col>
              </Row>

              <Divider style={{ borderColor: 'var(--color-border)' }} />

              <Title level={5} style={{ color: 'var(--color-text-primary)' }}>
                改进建议
              </Title>
              <List
                size="small"
                dataSource={report.suggestions}
                renderItem={(item, index) => (
                  <List.Item style={{ borderColor: 'var(--color-border)' }}>
                    <Text style={{ color: 'var(--color-text-secondary)' }}>
                      {index + 1}. {item}
                    </Text>
                  </List.Item>
                )}
              />
            </Card>
          </Col>

          {/* Detailed Report */}
          {report.detailed_report && (
            <Col xs={24}>
              <Card
                title="详细评估报告"
                style={{
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <div
                  style={{
                    maxHeight: '400px',
                    overflowY: 'auto',
                    padding: '16px',
                    background: 'var(--color-bg-primary)',
                    borderRadius: '8px',
                  }}
                >
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => (
                        <Title level={2} style={{ color: 'var(--color-text-primary)' }}>
                          {children}
                        </Title>
                      ),
                      h2: ({ children }) => (
                        <Title level={3} style={{ color: 'var(--color-text-primary)' }}>
                          {children}
                        </Title>
                      ),
                      p: ({ children }) => (
                        <Paragraph style={{ color: 'var(--color-text-secondary)' }}>
                          {children}
                        </Paragraph>
                      ),
                    }}
                  >
                    {report.detailed_report}
                  </ReactMarkdown>
                </div>
              </Card>
            </Col>
          )}

          {/* Reset Button */}
          <Col xs={24} style={{ textAlign: 'center' }}>
            <Button size="large" onClick={handleReset}>
              开始新的面试
            </Button>
          </Col>
        </Row>
      )}
    </div>
  )
}

export default InterviewSimulatorPage
