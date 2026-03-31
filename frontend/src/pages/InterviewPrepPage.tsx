import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Space,
  Typography,
  Radio,
  message,
  Spin,
  Steps,
} from 'antd'
import {
  RocketOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import type { PrepMode, InterviewQuestion } from '../types'
import { prepApi } from '../services/api'
import { QuestionPreview, AnswerRecording } from '../components/interview'

const { Text } = Typography

/**
 * 面试准备页面
 * 功能：
 * - 三种模式选择 (练习/模拟/挑战)
 * - 岗位技术栈配置表单
 * - 题目预览和难度选择
 * - 倒计时 Prep 界面 (30s/60s/90s 可选)
 */
const InterviewPrepPage: React.FC = () => {
  const [form] = Form.useForm()
  
  // 状态管理
  const [currentStep, setCurrentStep] = useState(0)
  const [mode, setMode] = useState<PrepMode>('practice')
  const [loading, setLoading] = useState(false)
  const [questions, setQuestions] = useState<InterviewQuestion[]>([])
  const [selectedQuestion, setSelectedQuestion] = useState<InterviewQuestion | null>(null)
  
  // 录音状态
  const [isRecording, setIsRecording] = useState(false)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const [prepTimeLeft, setPrepTimeLeft] = useState(0)
  const [isPreparing, setIsPreparing] = useState(false)
  
  // 准备时间选项
  const prepTimeOptions = [
    { value: 30, label: '30 秒' },
    { value: 60, label: '60 秒' },
    { value: 90, label: '90 秒' },
  ]
  const [selectedPrepTime, setSelectedPrepTime] = useState(60)

  // 模式配置
  const modeConfig = {
    practice: {
      title: '练习模式',
      description: '无压力练习，可反复尝试，即时反馈',
      icon: '🎯',
      color: '#1890ff',
    },
    mock: {
      title: '模拟模式',
      description: '全真模拟面试流程，完整评估报告',
      icon: '🎤',
      color: '#722ed1',
    },
    challenge: {
      title: '挑战模式',
      description: '高难度题目，限时作答，冲击高分',
      icon: '🔥',
      color: '#fa8c16',
    },
  }

  // 加载预习题
  const loadQuestions = async () => {
    setLoading(true)
    try {
      const values = await form.validateFields()
      const response = await prepApi.getPrepQuestions({
        mode,
        tech_stack: values.tech_stack?.split(',').map((s: string) => s.trim()) || [],
        difficulty: values.difficulty,
        limit: 10,
      })
      if (response.success && response.data) {
        setQuestions(response.data.questions)
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '加载题目失败'
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // 开始准备倒计时
  const startPrep = (question: InterviewQuestion) => {
    setSelectedQuestion(question)
    setPrepTimeLeft(selectedPrepTime)
    setIsPreparing(true)
  }

  // 准备倒计时
  useEffect(() => {
    if (!isPreparing || prepTimeLeft <= 0) return

    const timer = setInterval(() => {
      setPrepTimeLeft((prev) => {
        if (prev <= 1) {
          setIsPreparing(false)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [isPreparing, prepTimeLeft])

  // 录音计时器
  useEffect(() => {
    if (!isRecording) return

    const timer = setInterval(() => {
      setRecordingDuration((prev) => Math.min(prev + 1, 120))
    }, 1000)

    return () => clearInterval(timer)
  }, [isRecording])

  // 切换录音状态
  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false)
      message.success('录音已保存')
    } else {
      setIsRecording(true)
      setRecordingDuration(0)
    }
  }

  // 提交答案
  const submitAnswer = async () => {
    if (!selectedQuestion) return
    
    setLoading(true)
    try {
      // TODO: 实现答案提交逻辑
      message.success('答案已提交！正在分析...')
      setCurrentStep(3) // 跳转到反馈步骤
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : '提交失败'
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  // 渲染步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // 模式选择
        return (
          <Card title="选择面试模式">
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Radio.Group
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                style={{ width: '100%' }}
              >
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {(Object.keys(modeConfig) as PrepMode[]).map((m) => (
                    <Radio.Button
                      key={m}
                      value={m}
                      style={{
                        width: '100%',
                        padding: '20px',
                        height: 'auto',
                        textAlign: 'left',
                        borderRadius: 8,
                        border: mode === m ? `2px solid ${modeConfig[m].color}` : '1px solid #d9d9d9',
                      }}
                    >
                      <Space align="start">
                        <span style={{ fontSize: 32 }}>{modeConfig[m].icon}</span>
                        <div>
                          <Text strong style={{ fontSize: 16, display: 'block' }}>
                            {modeConfig[m].title}
                          </Text>
                          <Text type="secondary" style={{ fontSize: 13 }}>
                            {modeConfig[m].description}
                          </Text>
                        </div>
                      </Space>
                    </Radio.Button>
                  ))}
                </Space>
              </Radio.Group>
              <Button
                type="primary"
                size="large"
                onClick={() => setCurrentStep(1)}
                icon={<RocketOutlined />}
              >
                下一步：配置岗位
              </Button>
            </Space>
          </Card>
        )

      case 1: // 岗位配置
        return (
          <Card title="配置岗位要求">
            <Form form={form} layout="vertical" size="large">
              <Form.Item
                name="job_role"
                label="目标岗位"
                rules={[{ required: true, message: '请输入目标岗位' }]}
              >
                <Input placeholder="例如：前端开发工程师、Java 后端开发" />
              </Form.Item>

              <Form.Item
                name="tech_stack"
                label="技术栈（逗号分隔）"
                rules={[{ required: true, message: '请输入技术栈' }]}
              >
                <Input placeholder="例如：React, TypeScript, Node.js" />
              </Form.Item>

              <Form.Item
                name="difficulty"
                label="题目难度"
                initialValue="medium"
              >
                <Select>
                  <Select.Option value="easy">简单 - 基础概念为主</Select.Option>
                  <Select.Option value="medium">中等 - 结合实际应用</Select.Option>
                  <Select.Option value="hard">困难 - 深度原理和架构</Select.Option>
                </Select>
              </Form.Item>

              <Space>
                <Button onClick={() => setCurrentStep(0)}>上一步</Button>
                <Button
                  type="primary"
                  onClick={() => {
                    loadQuestions()
                    setCurrentStep(2)
                  }}
                  icon={<SettingOutlined />}
                >
                  开始准备
                </Button>
              </Space>
            </Form>
          </Card>
        )

      case 2: // 题目准备
        return (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card
              title={
                <Space>
                  <ClockCircleOutlined />
                  <span>准备答题</span>
                </Space>
              }
              extra={
                <Space>
                  <Text>准备时间：</Text>
                  <Radio.Group
                    value={selectedPrepTime}
                    onChange={(e) => setSelectedPrepTime(e.target.value)}
                    size="small"
                  >
                    {prepTimeOptions.map((opt) => (
                      <Radio.Button key={opt.value} value={opt.value}>
                        {opt.label}
                      </Radio.Button>
                    ))}
                  </Radio.Group>
                </Space>
              }
            >
              {loading ? (
                <Spin tip="加载中..." />
              ) : (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {questions.map((q) => (
                    <QuestionPreview
                      key={q.id}
                      question={q}
                      onSelect={startPrep}
                      showTips
                    />
                  ))}
                </Space>
              )}
            </Card>

            {/* 准备倒计时弹窗 */}
            {isPreparing && selectedQuestion && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                style={{
                  position: 'fixed',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'rgba(0,0,0,0.8)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  zIndex: 1000,
                }}
              >
                <Card
                  style={{ width: 400, textAlign: 'center' }}
                  actions={[
                    <Button
                      key="skip"
                      onClick={() => setIsPreparing(false)}
                      size="large"
                    >
                      跳过准备
                    </Button>,
                  ]}
                >
                  <Space direction="vertical" size="large">
                    <Typography.Title level={3}>
                      准备时间
                    </Typography.Title>
                    <div
                      style={{
                        fontSize: 72,
                        fontWeight: 'bold',
                        color: prepTimeLeft <= 10 ? '#ff4d4f' : '#1890ff',
                      }}
                    >
                      {prepTimeLeft}
                    </div>
                    <Text type="secondary">
                      {selectedQuestion.content.substring(0, 50)}...
                    </Text>
                  </Space>
                </Card>
              </motion.div>
            )}

            {/* 录音区域 */}
            {!isPreparing && selectedQuestion && prepTimeLeft === 0 && (
              <Card title="开始作答">
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <QuestionPreview question={selectedQuestion} compact />
                  <AnswerRecording
                    isRecording={isRecording}
                    duration={recordingDuration}
                    maxDuration={120}
                    status={isRecording ? 'recording' : recordingDuration > 0 ? 'completed' : 'recording'}
                    onToggle={toggleRecording}
                  />
                  <Button
                    type="primary"
                    size="large"
                    onClick={submitAnswer}
                    loading={loading}
                    disabled={recordingDuration === 0}
                    icon={<CheckCircleOutlined />}
                  >
                    提交答案
                  </Button>
                </Space>
              </Card>
            )}
          </Space>
        )

      case 3: // 反馈
        return (
          <Card title="答题反馈">
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div
                style={{
                  textAlign: 'center',
                  padding: '40px 0',
                }}
              >
                <CheckCircleOutlined
                  style={{ fontSize: 64, color: '#52c41a' }}
                />
                <Typography.Title level={3} style={{ marginTop: 16 }}>
                  答案已提交！
                </Typography.Title>
                <Text type="secondary">
                  AI 正在分析你的答案，请稍候查看详细反馈...
                </Text>
              </div>
              <Button
                type="primary"
                onClick={() => {
                  setCurrentStep(0)
                  setSelectedQuestion(null)
                  setRecordingDuration(0)
                }}
              >
                继续练习
              </Button>
            </Space>
          </Card>
        )

      default:
        return null
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '24px 0' }}>
      <Steps
        current={currentStep}
        items={[
          { title: '选择模式', icon: <RocketOutlined /> },
          { title: '配置岗位', icon: <SettingOutlined /> },
          { title: '准备答题', icon: <ClockCircleOutlined /> },
          { title: '查看反馈', icon: <CheckCircleOutlined /> },
        ]}
        style={{ marginBottom: 24 }}
      />
      {renderStepContent()}
    </div>
  )
}

export default InterviewPrepPage
