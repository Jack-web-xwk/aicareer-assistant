import { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  Upload,
  Input,
  Button,
  Steps,
  Progress,
  Space,
  message,
  Divider,
  Tag,
  List,
  Spin,
} from 'antd'
import {
  InboxOutlined,
  FileTextOutlined,
  SearchOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import ReactMarkdown from 'react-markdown'
import { resumeApi } from '../services/api'
import type { ResumeInfo, MatchAnalysis } from '../types'

const { Title, Paragraph, Text } = Typography
const { Dragger } = Upload
const { TextArea } = Input

function ResumeOptimizerPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [jobUrl, setJobUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [resumeId, setResumeId] = useState<number | null>(null)
  const [resumeInfo, setResumeInfo] = useState<ResumeInfo | null>(null)
  const [optimizedResume, setOptimizedResume] = useState<string>('')
  const [matchAnalysis, setMatchAnalysis] = useState<MatchAnalysis | null>(null)

  const steps = [
    { title: '上传简历', icon: <FileTextOutlined /> },
    { title: '输入目标岗位', icon: <SearchOutlined /> },
    { title: 'AI 优化中', icon: <RocketOutlined /> },
    { title: '查看结果', icon: <CheckCircleOutlined /> },
  ]

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.error('请先上传简历文件')
      return
    }

    const file = fileList[0].originFileObj
    if (!file) return

    setLoading(true)
    try {
      const response = await resumeApi.upload(file)
      if (response.success && response.data) {
        setResumeId(response.data.id)
        setCurrentStep(1)
        message.success('简历上传成功！')
      }
    } catch (error) {
      message.error(`上传失败: ${(error as Error).message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleOptimize = async () => {
    if (!resumeId) {
      message.error('请先上传简历')
      return
    }

    if (!jobUrl) {
      message.error('请输入目标岗位链接')
      return
    }

    setLoading(true)
    setCurrentStep(2)

    try {
      const response = await resumeApi.optimize(resumeId, jobUrl)
      if (response.success && response.data) {
        setResumeInfo(response.data)
        setOptimizedResume(response.data.optimized_resume || '')
        setMatchAnalysis(response.data.match_analysis || null)
        setCurrentStep(3)
        message.success('简历优化完成！')
      }
    } catch (error) {
      message.error(`优化失败: ${(error as Error).message}`)
      setCurrentStep(1)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    if (!resumeId) return

    try {
      const content = await resumeApi.download(resumeId, 'md')
      const blob = new Blob([content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `optimized_resume_${resumeId}.md`
      a.click()
      URL.revokeObjectURL(url)
      message.success('下载成功！')
    } catch (error) {
      message.error(`下载失败: ${(error as Error).message}`)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(optimizedResume)
    message.success('已复制到剪贴板！')
  }

  const handleReset = () => {
    setCurrentStep(0)
    setFileList([])
    setJobUrl('')
    setResumeId(null)
    setResumeInfo(null)
    setOptimizedResume('')
    setMatchAnalysis(null)
  }

  return (
    <div className="fade-in">
      <Title level={2} style={{ color: 'var(--color-text-primary)', marginBottom: '24px' }}>
        <FileTextOutlined style={{ marginRight: '12px', color: '#6366f1' }} />
        简历智能优化
      </Title>

      {/* Steps */}
      <Card
        style={{
          marginBottom: '24px',
          background: 'rgba(30, 41, 59, 0.5)',
          border: '1px solid var(--color-border)',
        }}
      >
        <Steps
          current={currentStep}
          items={steps.map((step) => ({
            title: step.title,
            icon: step.icon,
          }))}
        />
      </Card>

      {/* Step 0: Upload Resume */}
      {currentStep === 0 && (
        <Card
          style={{
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid var(--color-border)',
          }}
        >
          <Title level={4} style={{ color: 'var(--color-text-primary)' }}>
            第一步：上传你的简历
          </Title>
          <Paragraph style={{ color: 'var(--color-text-secondary)' }}>
            支持 PDF 和 Word (.docx) 格式，文件大小不超过 10MB
          </Paragraph>

          <Dragger
            fileList={fileList}
            onChange={({ fileList }) => setFileList(fileList.slice(-1))}
            beforeUpload={() => false}
            accept=".pdf,.docx,.doc"
            style={{ marginBottom: '24px' }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined style={{ color: '#6366f1', fontSize: '48px' }} />
            </p>
            <p className="ant-upload-text" style={{ color: 'var(--color-text-primary)' }}>
              点击或拖拽文件到此区域
            </p>
            <p className="ant-upload-hint" style={{ color: 'var(--color-text-muted)' }}>
              支持 PDF、Word 格式
            </p>
          </Dragger>

          <Button
            type="primary"
            size="large"
            onClick={handleUpload}
            loading={loading}
            disabled={fileList.length === 0}
            style={{ width: '100%' }}
          >
            上传简历
          </Button>
        </Card>
      )}

      {/* Step 1: Enter Job URL */}
      {currentStep === 1 && (
        <Card
          style={{
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid var(--color-border)',
          }}
        >
          <Title level={4} style={{ color: 'var(--color-text-primary)' }}>
            第二步：输入目标岗位链接
          </Title>
          <Paragraph style={{ color: 'var(--color-text-secondary)' }}>
            输入 Boss直聘 或其他招聘网站的岗位详情页链接，AI 将分析岗位需求并优化你的简历
          </Paragraph>

          <Input
            size="large"
            placeholder="例如: https://www.zhipin.com/job_detail/xxx"
            value={jobUrl}
            onChange={(e) => setJobUrl(e.target.value)}
            prefix={<SearchOutlined style={{ color: 'var(--color-text-muted)' }} />}
            style={{ marginBottom: '24px' }}
          />

          <Space style={{ width: '100%' }}>
            <Button onClick={handleReset}>重新上传</Button>
            <Button
              type="primary"
              size="large"
              onClick={handleOptimize}
              loading={loading}
              disabled={!jobUrl}
              style={{ flex: 1 }}
            >
              开始优化
            </Button>
          </Space>
        </Card>
      )}

      {/* Step 2: Processing */}
      {currentStep === 2 && (
        <Card
          style={{
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid var(--color-border)',
            textAlign: 'center',
            padding: '48px',
          }}
        >
          <Spin size="large" />
          <Title level={4} style={{ color: 'var(--color-text-primary)', marginTop: '24px' }}>
            AI 正在优化你的简历...
          </Title>
          <Paragraph style={{ color: 'var(--color-text-secondary)' }}>
            正在提取简历信息、分析岗位需求、匹配内容、生成优化简历
          </Paragraph>
          <Progress percent={75} status="active" strokeColor="#6366f1" />
        </Card>
      )}

      {/* Step 3: Results */}
      {currentStep === 3 && (
        <Row gutter={[24, 24]}>
          {/* Match Analysis */}
          {matchAnalysis && (
            <Col xs={24} lg={8}>
              <Card
                title="匹配分析"
                style={{
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid var(--color-border)',
                  height: '100%',
                }}
              >
                <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                  <Progress
                    type="circle"
                    percent={matchAnalysis.match_score}
                    strokeColor={{
                      '0%': '#6366f1',
                      '100%': '#8b5cf6',
                    }}
                    format={(percent) => (
                      <span style={{ color: 'var(--color-text-primary)', fontSize: '24px' }}>
                        {percent}%
                      </span>
                    )}
                  />
                  <div style={{ marginTop: '8px', color: 'var(--color-text-secondary)' }}>
                    匹配度
                  </div>
                </div>

                <Divider style={{ borderColor: 'var(--color-border)' }}>匹配技能</Divider>
                <div style={{ marginBottom: '16px' }}>
                  {matchAnalysis.matched_skills.map((skill, index) => (
                    <Tag key={index} color="success" style={{ marginBottom: '8px' }}>
                      {skill}
                    </Tag>
                  ))}
                </div>

                <Divider style={{ borderColor: 'var(--color-border)' }}>需补充技能</Divider>
                <div style={{ marginBottom: '16px' }}>
                  {matchAnalysis.missing_skills.map((skill, index) => (
                    <Tag key={index} color="warning" style={{ marginBottom: '8px' }}>
                      {skill}
                    </Tag>
                  ))}
                </div>

                <Divider style={{ borderColor: 'var(--color-border)' }}>优势</Divider>
                <List
                  size="small"
                  dataSource={matchAnalysis.strengths}
                  renderItem={(item) => (
                    <List.Item style={{ borderColor: 'var(--color-border)', padding: '8px 0' }}>
                      <Text style={{ color: 'var(--color-text-secondary)' }}>✓ {item}</Text>
                    </List.Item>
                  )}
                />

                <Divider style={{ borderColor: 'var(--color-border)' }}>改进建议</Divider>
                <List
                  size="small"
                  dataSource={matchAnalysis.suggestions}
                  renderItem={(item) => (
                    <List.Item style={{ borderColor: 'var(--color-border)', padding: '8px 0' }}>
                      <Text style={{ color: 'var(--color-text-secondary)' }}>→ {item}</Text>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          )}

          {/* Optimized Resume */}
          <Col xs={24} lg={matchAnalysis ? 16 : 24}>
            <Card
              title="优化后的简历"
              extra={
                <Space>
                  <Button icon={<CopyOutlined />} onClick={handleCopy}>
                    复制
                  </Button>
                  <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownload}>
                    下载 Markdown
                  </Button>
                </Space>
              }
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div
                style={{
                  maxHeight: '600px',
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
                    h3: ({ children }) => (
                      <Title level={4} style={{ color: 'var(--color-text-primary)' }}>
                        {children}
                      </Title>
                    ),
                    p: ({ children }) => (
                      <Paragraph style={{ color: 'var(--color-text-secondary)' }}>
                        {children}
                      </Paragraph>
                    ),
                    li: ({ children }) => (
                      <li style={{ color: 'var(--color-text-secondary)' }}>{children}</li>
                    ),
                    strong: ({ children }) => (
                      <Text strong style={{ color: 'var(--color-text-primary)' }}>
                        {children}
                      </Text>
                    ),
                  }}
                >
                  {optimizedResume}
                </ReactMarkdown>
              </div>
            </Card>

            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <Button size="large" onClick={handleReset}>
                优化另一份简历
              </Button>
            </div>
          </Col>
        </Row>
      )}
    </div>
  )
}

export default ResumeOptimizerPage
