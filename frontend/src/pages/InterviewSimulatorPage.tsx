import { useState, useRef, useEffect, useCallback } from 'react'
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
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { interviewApi } from '../services/api'
import type { InterviewSession, InterviewReport, WSMessage, SSEMessage } from '../types'

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
}

function InterviewSimulatorPage() {
  // State
  const [stage, setStage] = useState<'setup' | 'interview' | 'report'>('setup')
  const [jobRole, setJobRole] = useState('')
  const [techStack, setTechStack] = useState<string[]>([])
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium')
  const [loading, setLoading] = useState(false)
  
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const [report, setReport] = useState<InterviewReport | null>(null)
  
  // WebSocket
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

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
      })

      if (response.success && response.data) {
        setSession(response.data)
        setMessages([
          {
            role: 'assistant',
            content: response.data.current_question || '面试开始！',
            timestamp: new Date(),
          },
        ])
        setStage('interview')
        message.success('面试开始！')

        // Setup WebSocket for real-time communication
        const ws = interviewApi.createWebSocket(response.data.session_id)
        wsRef.current = ws

        ws.onmessage = (event) => {
          const data: WSMessage = JSON.parse(event.data)
          
          if (data.type === 'response') {
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
      message.error(`开始面试失败: ${(error as Error).message}`)
    } finally {
      setLoading(false)
    }
  }

  // Send answer
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
            if (data.type === 'start') {
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
            maxWidth: '600px',
            margin: '0 auto',
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid var(--color-border)',
          }}
        >
          <Title level={4} style={{ color: 'var(--color-text-primary)' }}>
            配置面试参数
          </Title>

          <div style={{ marginBottom: '24px' }}>
            <Text style={{ color: 'var(--color-text-secondary)', display: 'block', marginBottom: '8px' }}>
              目标岗位
            </Text>
            <Input
              size="large"
              placeholder="例如: Python 后端工程师"
              value={jobRole}
              onChange={(e) => setJobRole(e.target.value)}
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
                                msg.content
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
                  >
                    发送
                  </Button>
                </Space.Compact>
                <Text
                  type="secondary"
                  style={{ fontSize: '12px', display: 'block', marginTop: '8px' }}
                >
                  提示: 按 Enter 发送，Shift + Enter 换行
                </Text>
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
