import type { ReactNode } from 'react'
import { Card, Row, Col, Typography, Button, Space, Divider } from 'antd'
import {
  FileTextOutlined,
  AudioOutlined,
  RocketOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  ApiOutlined,
  SearchOutlined,
  LinkOutlined,
  FolderOpenOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

function HomePage() {
  const navigate = useNavigate()

  const features = [
    {
      icon: <FileTextOutlined style={{ fontSize: '32px', color: '#6366f1' }} />,
      title: '简历智能优化',
      description: '上传或选用已有简历 + 目标岗位链接，LangGraph 工作流分析匹配度并流式生成优化简历。',
      action: () => navigate('/resume'),
      buttonText: '开始优化',
    },
    {
      icon: <AudioOutlined style={{ fontSize: '32px', color: '#8b5cf6' }} />,
      title: '语音面试模拟',
      description: '选择目标岗位和技术栈，与 AI 面试官进行语音对话，获得实时反馈和评估报告。',
      action: () => navigate('/interview'),
      buttonText: '开始面试',
    },
  ]

  const moreFeatures: {
    icon: ReactNode
    title: string
    description: string
    action: () => void
    buttonText: string
  }[] = [
    {
      icon: <SearchOutlined style={{ fontSize: '28px', color: '#22d3ee' }} />,
      title: '多源职位搜索',
      description: 'Boss / 智联 / 鱼泡等聚合搜索，支持筛选、排序与分页，结果可保存。',
      action: () => navigate('/jobs'),
      buttonText: '去搜索',
    },
    {
      icon: <LinkOutlined style={{ fontSize: '28px', color: '#f472b6' }} />,
      title: '目标岗位（链接 / 截图）',
      description: '粘贴详情页 URL 自动爬取，或上传截图由多模态模型抽取岗位信息并入库。',
      action: () => navigate('/target-jobs'),
      buttonText: '去添加',
    },
    {
      icon: <FolderOpenOutlined style={{ fontSize: '28px', color: '#a78bfa' }} />,
      title: '我的职位',
      description: '查看已保存的职位记录（搜索收藏与链接爬取入库统一管理）。',
      action: () => navigate('/jobs/saved'),
      buttonText: '打开职位库',
    },
    {
      icon: <HistoryOutlined style={{ fontSize: '28px', color: '#94a3b8' }} />,
      title: '简历任务 / 历史',
      description: '全部上传与优化任务、继续流式优化、解除卡住、下载结果；面试报告也在此查看。',
      action: () => navigate('/resume/history'),
      buttonText: '查看历史',
    },
  ]

  const techHighlights = [
    {
      icon: <ThunderboltOutlined />,
      title: 'LangGraph 智能体',
      description: '基于状态图的 AI 工作流，精准控制每个处理步骤',
    },
    {
      icon: <ApiOutlined />,
      title: 'OpenAI 集成',
      description: 'GPT-4o-mini 文本生成 + Whisper 语音识别 + TTS 语音合成',
    },
    {
      icon: <SafetyOutlined />,
      title: '企业级架构',
      description: 'FastAPI 异步框架 + SQLAlchemy ORM + WebSocket 实时通信',
    },
  ]

  return (
    <div className="fade-in">
      {/* Hero Section */}
      <div
        style={{
          textAlign: 'center',
          padding: '60px 20px',
          marginBottom: '48px',
        }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <RocketOutlined
            style={{
              fontSize: '64px',
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          />
          <Title
            level={1}
            style={{
              fontSize: '48px',
              margin: 0,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            AI 求职助手
          </Title>
          <Paragraph
            style={{
              fontSize: '18px',
              color: 'var(--color-text-secondary)',
              maxWidth: '600px',
              margin: '0 auto',
            }}
          >
            基于 FastAPI + LangGraph 的智能求职工具，
            <br />
            帮助你优化简历、模拟技术面试，提升求职成功率
          </Paragraph>
        </Space>
      </div>

      {/* Feature Cards */}
      <Row gutter={[24, 24]} style={{ marginBottom: '48px' }}>
        {features.map((feature, index) => (
          <Col xs={24} md={12} key={index}>
            <Card
              hoverable
              style={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%)',
                border: '1px solid var(--color-border)',
                transition: 'all 0.3s ease',
              }}
              bodyStyle={{ padding: '32px' }}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {feature.icon}
                <Title level={3} style={{ color: 'var(--color-text-primary)', margin: 0 }}>
                  {feature.title}
                </Title>
                <Paragraph style={{ color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
                  {feature.description}
                </Paragraph>
                <Button
                  type="primary"
                  size="large"
                  onClick={feature.action}
                  style={{ width: '100%' }}
                >
                  {feature.buttonText}
                </Button>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      <Divider plain style={{ borderColor: 'var(--color-border)', margin: '8px 0 32px' }}>
        <Text style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>新增与扩展能力</Text>
      </Divider>

      <Row gutter={[24, 24]} style={{ marginBottom: '48px' }}>
        {moreFeatures.map((feature, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card
              hoverable
              style={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.9) 100%)',
                border: '1px solid var(--color-border)',
              }}
              bodyStyle={{ padding: '24px' }}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {feature.icon}
                <Title level={4} style={{ color: 'var(--color-text-primary)', margin: 0, fontSize: 17 }}>
                  {feature.title}
                </Title>
                <Paragraph
                  style={{ color: 'var(--color-text-secondary)', marginBottom: 8, minHeight: 72, fontSize: 13 }}
                >
                  {feature.description}
                </Paragraph>
                <Button type="default" block onClick={feature.action}>
                  {feature.buttonText}
                </Button>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Tech Highlights */}
      <Card
        style={{
          background: 'rgba(30, 41, 59, 0.5)',
          border: '1px solid var(--color-border)',
        }}
      >
        <Title level={4} style={{ color: 'var(--color-text-primary)', textAlign: 'center', marginBottom: '32px' }}>
          技术亮点
        </Title>
        <Row gutter={[24, 24]}>
          {techHighlights.map((item, index) => (
            <Col xs={24} md={8} key={index}>
              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px',
                    fontSize: '24px',
                    color: '#6366f1',
                  }}
                >
                  {item.icon}
                </div>
                <Title level={5} style={{ color: 'var(--color-text-primary)', marginBottom: '8px' }}>
                  {item.title}
                </Title>
                <Text style={{ color: 'var(--color-text-muted)' }}>
                  {item.description}
                </Text>
              </div>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  )
}

export default HomePage
