import { useState, useEffect } from 'react'
import { Modal, Steps, Button, Typography, Space } from 'antd'
import {
  FileTextOutlined,
  SearchOutlined,
  AudioOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

/** 引导步骤配置 */
const ONBOARDING_STEPS = [
  {
    title: '上传简历',
    icon: <FileTextOutlined />,
    description: '上传你的简历，AI 将基于目标岗位进行智能分析和优化建议，帮你打造更有竞争力的简历。',
    color: '#6366f1',
    route: '/resume',
  },
  {
    title: '搜索职位',
    icon: <SearchOutlined />,
    description: '搜索 Boss、智联、鱼泡等多平台职位信息，支持按岗位链接自动爬取，快速建立你的目标职位库。',
    color: '#22d3ee',
    route: '/jobs',
  },
  {
    title: '开始面试',
    icon: <AudioOutlined />,
    description: '选择目标岗位，与 AI 面试官进行语音对话模拟面试，获取实时反馈和详细评估报告。',
    color: '#8b5cf6',
    route: '/interview',
  },
]

const STORAGE_KEY = 'onboarding_completed'

/**
 * 用户 Onboarding 引导组件
 * 首次访问时显示 3 步引导，完成后写入 localStorage 标记
 */
function OnboardingGuide() {
  const navigate = useNavigate()
  const [visible, setVisible] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    const completed = localStorage.getItem(STORAGE_KEY)
    if (!completed) {
      setVisible(true)
    }
  }, [])

  /** 跳过引导 */
  const handleSkip = () => {
    localStorage.setItem(STORAGE_KEY, 'true')
    setVisible(false)
  }

  /** 下一步 */
  const handleNext = () => {
    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      // 最后一步，完成引导
      handleComplete()
    }
  }

  /** 完成引导并跳转 */
  const handleComplete = () => {
    localStorage.setItem(STORAGE_KEY, 'true')
    setVisible(false)
    const targetRoute = ONBOARDING_STEPS[currentStep].route
    navigate(targetRoute)
  }

  /** 上一步 */
  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const step = ONBOARDING_STEPS[currentStep]
  const isLastStep = currentStep === ONBOARDING_STEPS.length - 1
  const isFirstStep = currentStep === 0

  return (
    <Modal
      open={visible}
      closable={false}
      footer={null}
      centered
      width={560}
      styles={{
        body: {
          padding: '40px 32px 32px',
          borderRadius: '12px',
        },
      }}
    >
      {/* 标题区域 */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <RocketOutlined
          style={{
            fontSize: 40,
            color: '#6366f1',
            marginBottom: 16,
          }}
        />
        <Title level={3} style={{ margin: '8px 0 4px' }}>
          欢迎使用 AI 求职助手
        </Title>
        <Text type="secondary">三个简单步骤，开启你的智能求职之旅</Text>
      </div>

      {/* 步骤指示器 */}
      <Steps
        current={currentStep}
        size="small"
        items={ONBOARDING_STEPS.map((s) => ({
          title: s.title,
          icon: s.icon,
        }))}
        style={{ marginBottom: 32 }}
      />

      {/* 当前步骤内容 */}
      <div
        style={{
          textAlign: 'center',
          padding: '24px 16px',
          background: 'rgba(99, 102, 241, 0.06)',
          borderRadius: 12,
          marginBottom: 32,
          minHeight: 160,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: 16,
            background: `${step.color}20`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 32,
            color: step.color,
            marginBottom: 16,
          }}
        >
          {step.icon}
        </div>
        <Title level={4} style={{ margin: '0 0 8px', color: step.color }}>
          {step.title}
        </Title>
        <Paragraph
          style={{
            color: 'var(--color-text-secondary, #666)',
            margin: 0,
            fontSize: 14,
            lineHeight: 1.6,
            maxWidth: 420,
          }}
        >
          {step.description}
        </Paragraph>
      </div>

      {/* 按钮区域 */}
      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Button onClick={handleSkip} type="text" style={{ color: '#999' }}>
          跳过引导
        </Button>
        <Space>
          {!isFirstStep && (
            <Button onClick={handlePrev}>
              上一步
            </Button>
          )}
          <Button type="primary" onClick={handleNext}>
            {isLastStep ? '立即开始' : '下一步'}
          </Button>
        </Space>
      </Space>
    </Modal>
  )
}

export default OnboardingGuide
