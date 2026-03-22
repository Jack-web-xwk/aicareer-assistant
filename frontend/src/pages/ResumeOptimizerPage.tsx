import {
  useState,
  useCallback,
  useEffect,
  useRef,
  useMemo,
  type CSSProperties,
  type ReactNode,
} from 'react'
import { flushSync } from 'react-dom'
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
  Timeline,
  Alert,
  Drawer,
  Segmented,
  Select,
  Collapse,
} from 'antd'
import {
  InboxOutlined,
  FileTextOutlined,
  SearchOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  DownloadOutlined,
  CopyOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import ReactMarkdown from 'react-markdown'
import { Link, useSearchParams } from 'react-router-dom'
import { jobSavedApi, resumeApi } from '../services/api'
import type {
  MatchAnalysis,
  ResumeInfo,
  ResumeOptimizerGraphNode,
  ResumeNodeOutputPayload,
  ResumeStreamMessage,
  ResumeStatus,
  ResumeUploadListItem,
  StudyQaItem,
} from '../types'

const { Title, Paragraph, Text } = Typography
const { Dragger } = Upload

/** 与后端 LangGraph StateGraph 节点名一致 */
const GRAPH_NODES: { key: ResumeOptimizerGraphNode; label: string }[] = [
  { key: 'extract_resume_info', label: '提取简历信息' },
  { key: 'analyze_job_requirements', label: '分析岗位需求' },
  { key: 'match_content', label: '内容匹配分析' },
  { key: 'generate_optimized_resume', label: '生成优化简历（流式）' },
]

type PipelineStatus = 'pending' | 'active' | 'done' | 'error'

function createInitialPipeline(): Record<ResumeOptimizerGraphNode, PipelineStatus> {
  return {
    extract_resume_info: 'pending',
    analyze_job_requirements: 'pending',
    match_content: 'pending',
    generate_optimized_resume: 'pending',
  }
}

const RESUME_STATUS_SHORT: Record<ResumeStatus, string> = {
  uploaded: '已上传',
  parsing: '解析中',
  parsed: '待优化',
  optimizing: '优化中',
  optimized: '已完成',
  failed: '失败',
}

function ResumeOptimizerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const resumeIdFromQuery = searchParams.get('resumeId')

  const [currentStep, setCurrentStep] = useState(0)
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [jobUrl, setJobUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [resumeId, setResumeId] = useState<number | null>(null)
  const [optimizedResume, setOptimizedResume] = useState<string>('')
  const [matchAnalysis, setMatchAnalysis] = useState<MatchAnalysis | null>(null)
  const [progressPercent, setProgressPercent] = useState(0)
  const [progressText, setProgressText] = useState('准备开始...')
  const [pipeline, setPipeline] = useState<Record<ResumeOptimizerGraphNode, PipelineStatus>>(
    createInitialPipeline
  )
  /** 与后端简历状态同步，用于轮询「优化中」任务 */
  const [resumeStatus, setResumeStatus] = useState<ResumeStatus | null>(null)
  const [resumeErrorMessage, setResumeErrorMessage] = useState<string | null>(null)
  /** 学习问答（面试准备），按 resumeId 清空 */
  const [studyQaItems, setStudyQaItems] = useState<StudyQaItem[]>([])
  const [studyQaLoading, setStudyQaLoading] = useState(false)
  /** 本页正在接收 SSE 流时为 true，避免与轮询重复请求 */
  const streamActiveRef = useRef(false)

  /** LangGraph 各节点 SSE 返回的结构化数据 + 思考说明 */
  const [nodeOutputs, setNodeOutputs] = useState<
    Partial<Record<ResumeOptimizerGraphNode, ResumeNodeOutputPayload>>
  >({})
  const [selectedNodeKey, setSelectedNodeKey] = useState<ResumeOptimizerGraphNode | null>(null)

  /** 第一步：上传新文件 或 从服务器已上传列表中选择 */
  const [resumeInputMode, setResumeInputMode] = useState<'upload' | 'existing'>('upload')
  const [existingResumes, setExistingResumes] = useState<ResumeUploadListItem[]>([])
  const [existingListLoading, setExistingListLoading] = useState(false)
  const [selectedExistingId, setSelectedExistingId] = useState<number | null>(null)

  const setProgressForNode = useCallback((nodeKey: ResumeOptimizerGraphNode) => {
    const idx = GRAPH_NODES.findIndex((n) => n.key === nodeKey)
    if (idx < 0) return
    setProgressPercent(20 + Math.round((idx / GRAPH_NODES.length) * 55))
  }, [])

  const applyProgressNode = useCallback((nodeKey: ResumeOptimizerGraphNode) => {
    setPipeline((prev) => {
      const next = { ...prev }
      const order = GRAPH_NODES.map((n) => n.key)
      const idx = order.indexOf(nodeKey)
      for (let i = 0; i < order.length; i++) {
        if (i < idx) next[order[i]] = 'done'
        else if (i === idx) next[order[i]] = 'active'
        else next[order[i]] = 'pending'
      }
      return next
    })
    setProgressForNode(nodeKey)
  }, [setProgressForNode])

  const applyGeneratePhase = useCallback(() => {
    setPipeline((prev) => ({
      ...prev,
      extract_resume_info: 'done',
      analyze_job_requirements: 'done',
      match_content: 'done',
      generate_optimized_resume: 'active',
    }))
    setProgressPercent(88)
  }, [])

  const applyAllDone = useCallback(() => {
    setPipeline({
      extract_resume_info: 'done',
      analyze_job_requirements: 'done',
      match_content: 'done',
      generate_optimized_resume: 'done',
    })
    setProgressPercent(100)
  }, [])

  const setPipelineRemoteOptimizing = useCallback(() => {
    setPipeline({
      extract_resume_info: 'done',
      analyze_job_requirements: 'done',
      match_content: 'done',
      generate_optimized_resume: 'active',
    })
    setProgressPercent(75)
  }, [])

  /** 根据 GET /resume/{id} 详情同步本页步骤与状态（URL 带入与「选用已有简历」共用） */
  const applyResumeDetail = useCallback(
    (r: ResumeInfo) => {
      setResumeId(r.id)
      setJobUrl(r.target_job_url || '')
      setResumeErrorMessage(null)
      setResumeStatus(r.status)

      if (r.status === 'optimized') {
        setOptimizedResume(r.optimized_resume || '')
        setMatchAnalysis(r.match_analysis ?? null)
        applyAllDone()
        setCurrentStep(3)
        setProgressPercent(100)
        setProgressText('优化完成')
        return
      }
      if (r.status === 'optimizing') {
        setCurrentStep(2)
        setPipelineRemoteOptimizing()
        setProgressText(
          '优化进行中…（关闭页面后任务仍在后台执行，将自动刷新结果）'
        )
        setOptimizedResume(r.optimized_resume || '')
        return
      }
      if (r.status === 'failed') {
        setResumeErrorMessage(r.error_message || '优化失败')
        setCurrentStep(1)
        setProgressPercent(0)
        setProgressText('准备开始...')
        setPipeline(createInitialPipeline())
        return
      }
      if (r.status === 'parsed') {
        setCurrentStep(1)
        return
      }
      setCurrentStep(0)
    },
    [applyAllDone, setPipelineRemoteOptimizing]
  )

  /** 从「目标岗位搜索」等入口带 ?targetJobUrl= 预填链接 */
  const targetJobUrlFromQuery = searchParams.get('targetJobUrl')
  useEffect(() => {
    if (!targetJobUrlFromQuery) return
    try {
      setJobUrl(decodeURIComponent(targetJobUrlFromQuery))
    } catch {
      setJobUrl(targetJobUrlFromQuery)
    }
  }, [targetJobUrlFromQuery])

  /** 从「截图保存」入口带 ?savedJobId= 加载伪链接 job:screenshot:… */
  const savedJobIdFromQuery = searchParams.get('savedJobId')
  useEffect(() => {
    if (!savedJobIdFromQuery) return
    const id = parseInt(savedJobIdFromQuery, 10)
    if (Number.isNaN(id)) return
    let cancelled = false
    void (async () => {
      try {
        const res = await jobSavedApi.get(id)
        if (cancelled || !res.success || !res.data) return
        setJobUrl(res.data.detail_url)
        message.success('已载入截图保存的职位')
      } catch (e) {
        message.error(`加载已保存职位失败: ${(e as Error).message}`)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [savedJobIdFromQuery])

  /** 从「历史结果」等入口带 ?resumeId= 恢复工作流界面 */
  useEffect(() => {
    if (!resumeIdFromQuery) return
    const id = parseInt(resumeIdFromQuery, 10)
    if (Number.isNaN(id)) return
    let cancelled = false
    void (async () => {
      setLoading(true)
      try {
        const res = await resumeApi.get(id)
        if (cancelled || !res.success || !res.data) return
        applyResumeDetail(res.data)
      } catch (e) {
        message.error(`加载任务失败: ${(e as Error).message}`)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [resumeIdFromQuery, applyResumeDetail])

  /** 远程「优化中」时轮询详情，直至完成或失败（本页未连接 SSE 时） */
  useEffect(() => {
    if (!resumeId || resumeStatus !== 'optimizing') return
    if (streamActiveRef.current) return

    const interval = setInterval(async () => {
      try {
        const res = await resumeApi.get(resumeId)
        if (!res.success || !res.data) return
        const r = res.data
        setResumeStatus(r.status)
        if (r.optimized_resume) {
          setOptimizedResume(r.optimized_resume)
        }
        if (r.status === 'optimized') {
          setOptimizedResume(r.optimized_resume || '')
          setMatchAnalysis(r.match_analysis ?? null)
          applyAllDone()
          setCurrentStep(3)
          setProgressPercent(100)
          setProgressText('优化完成')
          message.success('简历优化已完成')
          clearInterval(interval)
        }
        if (r.status === 'failed') {
          setResumeErrorMessage(r.error_message || '优化失败')
          setCurrentStep(1)
          setProgressPercent(0)
          setProgressText('准备开始...')
          setPipeline(createInitialPipeline())
          message.error(r.error_message || '优化失败')
          clearInterval(interval)
        }
      } catch {
        /* 忽略单次轮询错误 */
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [resumeId, resumeStatus, applyAllDone])

  useEffect(() => {
    setStudyQaItems([])
  }, [resumeId])

  const handleGenerateStudyQa = useCallback(async () => {
    if (resumeId == null) return
    setStudyQaLoading(true)
    try {
      const res = await resumeApi.studyQa(resumeId)
      if (res.success && res.data?.items?.length) {
        setStudyQaItems(res.data.items)
        message.success('已生成学习问答')
      } else {
        message.error(res.message || '生成失败')
      }
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setStudyQaLoading(false)
    }
  }, [resumeId])

  /** 第一步进入时拉取已上传简历列表，供「使用已有简历」 */
  useEffect(() => {
    if (currentStep !== 0) return
    void (async () => {
      setExistingListLoading(true)
      try {
        const res = await resumeApi.list(0, 100)
        if (res.success && res.data?.resumes) {
          setExistingResumes(res.data.resumes)
        } else {
          setExistingResumes([])
        }
      } catch (e) {
        message.error(`加载已有简历列表失败: ${(e as Error).message}`)
        setExistingResumes([])
      } finally {
        setExistingListLoading(false)
      }
    })()
  }, [currentStep])

  /** 第一步停留在「已上传/解析中」时轮询直到可进入岗位链接步骤 */
  useEffect(() => {
    if (currentStep !== 0 || resumeId == null) return
    if (resumeStatus !== 'uploaded' && resumeStatus !== 'parsing') return

    const interval = setInterval(async () => {
      try {
        const res = await resumeApi.get(resumeId)
        if (!res.success || !res.data) return
        const r = res.data
        setResumeStatus(r.status)
        if (r.status === 'parsed') {
          message.success('简历已解析完成')
          setCurrentStep(1)
          clearInterval(interval)
        }
        if (r.status === 'failed') {
          setResumeErrorMessage(r.error_message || '简历处理失败')
          message.error(r.error_message || '简历处理失败')
          clearInterval(interval)
        }
        if (r.status === 'optimizing' || r.status === 'optimized') {
          applyResumeDetail(r)
          clearInterval(interval)
        }
      } catch {
        /* 忽略单次轮询错误 */
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [currentStep, resumeId, resumeStatus, applyResumeDetail])

  const steps = [
    { title: '上传简历', icon: <FileTextOutlined /> },
    { title: '准备优化', icon: <SearchOutlined /> },
    { title: 'AI 优化中', icon: <RocketOutlined /> },
    { title: '查看结果', icon: <CheckCircleOutlined /> },
  ]

  const cardStyle: CSSProperties = {
    background: 'var(--color-bg-primary)',
    border: '1px solid var(--color-border)',
    boxShadow: 'var(--shadow-sm)',
  }

  const handleUseExistingResume = async () => {
    if (selectedExistingId == null) {
      message.warning('请先选择一份简历')
      return
    }
    setLoading(true)
    try {
      const res = await resumeApi.get(selectedExistingId)
      if (!res.success || !res.data) {
        message.error(res.message || '加载简历失败')
        return
      }
      applyResumeDetail(res.data)
      setSearchParams({ resumeId: String(res.data.id) }, { replace: true })
      message.success('已载入所选简历')
    } catch (error) {
      message.error(`载入失败: ${(error as Error).message}`)
    } finally {
      setLoading(false)
    }
  }

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
        setSearchParams({}, { replace: true })
        setResumeStatus(null)
        setResumeErrorMessage(null)
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
    setProgressPercent(8)
    setProgressText('连接流式服务...')
    setOptimizedResume('')
    setMatchAnalysis(null)
    setPipeline(createInitialPipeline())
    setResumeStatus('optimizing')
    streamActiveRef.current = true
    setNodeOutputs({})
    setSelectedNodeKey(null)

    try {
      await resumeApi.optimizeStream(
        resumeId,
        (event: ResumeStreamMessage) => {
          const nodeId = event.node ?? event.step

          if (event.type === 'node_complete' && event.node) {
            setNodeOutputs((prev) => ({
              ...prev,
              [event.node as ResumeOptimizerGraphNode]: {
                data: event.data,
                thinking: event.thinking ?? undefined,
                rawPreview: event.raw_preview ?? undefined,
              },
            }))
            return
          }

          if (event.type === 'start') {
            setProgressText(event.message || '开始优化...')
            setProgressPercent(12)
            return
          }

          if (event.type === 'progress' && nodeId) {
            applyProgressNode(nodeId)
            setProgressText(event.message || '处理中...')
            return
          }

          if (event.type === 'token') {
            applyGeneratePhase()
            setProgressText('正在流式生成优化简历...')
            flushSync(() => {
              setOptimizedResume((prev) => prev + (event.delta || ''))
            })
            return
          }

          if (event.type === 'done') {
            const finalResume = event.optimized_resume || ''
            applyAllDone()
            setProgressText('优化完成')
            setOptimizedResume(finalResume)
            setMatchAnalysis(event.match_analysis || null)
            setCurrentStep(3)
            setResumeStatus('optimized')
            message.success('简历优化完成！')
            return
          }

          if (event.type === 'error') {
            setPipeline((prev) => {
              const active = (Object.entries(prev).find(([, v]) => v === 'active')?.[0] ??
                'generate_optimized_resume') as ResumeOptimizerGraphNode
              return { ...prev, [active]: 'error' }
            })
            setLoading(false)
            setCurrentStep(1)
            setProgressPercent(0)
            setProgressText('优化失败')
            setResumeStatus('failed')
            setResumeErrorMessage(event.message || '流式优化失败')
            message.error(`优化失败: ${event.message || '流式优化失败'}`)
          }
        },
        jobUrl,
        (error) => message.error(`优化失败: ${error.message}`)
      )
    } catch (error) {
      message.error(`优化失败: ${(error as Error).message}`)
      setCurrentStep(1)
      setResumeStatus('failed')
      setResumeErrorMessage((error as Error).message)
    } finally {
      streamActiveRef.current = false
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
    setSearchParams({}, { replace: true })
    setCurrentStep(0)
    setResumeInputMode('upload')
    setSelectedExistingId(null)
    setFileList([])
    setJobUrl('')
    setResumeId(null)
    setOptimizedResume('')
    setMatchAnalysis(null)
    setProgressPercent(0)
    setProgressText('准备开始...')
    setPipeline(createInitialPipeline())
    setResumeStatus(null)
    setResumeErrorMessage(null)
    setNodeOutputs({})
    setSelectedNodeKey(null)
  }

  const markdownComponents = {
    h1: ({ children }: { children?: ReactNode }) => (
      <Title level={2} style={{ color: 'var(--color-text-primary)' }}>
        {children}
      </Title>
    ),
    h2: ({ children }: { children?: ReactNode }) => (
      <Title level={3} style={{ color: 'var(--color-text-primary)' }}>
        {children}
      </Title>
    ),
    h3: ({ children }: { children?: ReactNode }) => (
      <Title level={4} style={{ color: 'var(--color-text-primary)' }}>
        {children}
      </Title>
    ),
    p: ({ children }: { children?: ReactNode }) => (
      <Paragraph style={{ color: 'var(--color-text-secondary)' }}>{children}</Paragraph>
    ),
    li: ({ children }: { children?: ReactNode }) => (
      <li style={{ color: 'var(--color-text-secondary)' }}>{children}</li>
    ),
    strong: ({ children }: { children?: ReactNode }) => (
      <Text strong style={{ color: 'var(--color-text-primary)' }}>
        {children}
      </Text>
    ),
  }

  const langGraphTimelineItems = useMemo(
    () =>
      GRAPH_NODES.map(({ key, label }) => {
        const st = pipeline[key]
        const hasDetail = Boolean(nodeOutputs[key]?.data || nodeOutputs[key]?.thinking)
        let color = 'gray'
        let dot: ReactNode = <ClockCircleOutlined />
        if (st === 'done') {
          color = 'green'
          dot = <CheckCircleOutlined />
        } else if (st === 'active') {
          color = 'blue'
          dot = <LoadingOutlined spin />
        } else if (st === 'error') {
          color = 'red'
        }
        return {
          color,
          dot,
          children: (
            <div
              role="button"
              tabIndex={0}
              onClick={() => setSelectedNodeKey(key)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  setSelectedNodeKey(key)
                }
              }}
              style={{
                cursor: 'pointer',
                padding: '6px 4px',
                borderRadius: 6,
                border: '1px solid transparent',
              }}
            >
              <Space align="start" wrap>
                <div>
                  <Text strong style={{ color: 'var(--color-text-primary)' }}>
                    {label}
                  </Text>
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {key}
                    </Text>
                  </div>
                </div>
                {hasDetail ? <Tag color="processing">有输出</Tag> : null}
              </Space>
            </div>
          ),
        }
      }),
    [pipeline, nodeOutputs]
  )

  const selectedNodeDetail = selectedNodeKey ? nodeOutputs[selectedNodeKey] : undefined

  return (
    <div className="fade-in">
      <Space
        align="center"
        style={{ marginBottom: 24, width: '100%', justifyContent: 'space-between' }}
      >
        <Title level={2} style={{ color: 'var(--color-text-primary)', margin: 0 }}>
          <FileTextOutlined style={{ marginRight: '12px', color: 'var(--color-primary)' }} />
          简历智能优化
        </Title>
        <Space>
          <Link to="/target-jobs">
            <Button icon={<SearchOutlined />}>目标岗位（链接）</Button>
          </Link>
          <Link to="/resume/history">
            <Button icon={<HistoryOutlined />}>简历任务 / 历史</Button>
          </Link>
        </Space>
      </Space>

      <Paragraph type="secondary" style={{ marginBottom: '16px' }}>
        优化过程基于 LangGraph 工作流：下方时间线会展示各节点执行状态；最后一步为流式生成，右侧可实时预览 Markdown。
      </Paragraph>

      <Card style={{ marginBottom: '24px', ...cardStyle }}>
        <Steps
          current={currentStep}
          items={steps.map((step) => ({
            title: step.title,
            icon: step.icon,
          }))}
        />
      </Card>

      {currentStep === 0 && (
        <Card style={cardStyle}>
          <Title level={4} style={{ color: 'var(--color-text-primary)' }}>
            第一步：上传或选择简历
          </Title>
          <Paragraph type="secondary">
            可上传新文件，或从已保存到服务器的简历中选择一份继续（解析完成后进入岗位链接步骤）。
          </Paragraph>

          {resumeId != null &&
          (resumeStatus === 'parsing' || resumeStatus === 'uploaded') ? (
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
              message="正在解析简历"
              description="解析完成后会自动进入「准备优化」步骤；也可关闭页面后从历史任务继续。"
            />
          ) : null}

          <Segmented
            options={[
              { label: '上传新文件', value: 'upload' },
              { label: '使用已有简历', value: 'existing' },
            ]}
            value={resumeInputMode}
            onChange={(v) => setResumeInputMode(v as 'upload' | 'existing')}
            block
            style={{ marginBottom: 20 }}
          />

          {resumeInputMode === 'upload' ? (
            <>
              <Paragraph type="secondary">
                支持 PDF 和 Word (.docx) 格式，文件大小不超过 10MB
              </Paragraph>
              <Dragger
                fileList={fileList}
                onChange={({ fileList: fl }) => setFileList(fl.slice(-1))}
                beforeUpload={() => false}
                accept=".pdf,.docx,.doc"
                style={{ marginBottom: '24px' }}
              >
                <p className="ant-upload-drag-icon">
                  <InboxOutlined style={{ color: 'var(--color-primary)', fontSize: '48px' }} />
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
            </>
          ) : (
            <Spin spinning={existingListLoading}>
              <Paragraph type="secondary" style={{ marginBottom: 12 }}>
                下列为当前账号已上传的简历记录，任选其一载入工作流。
              </Paragraph>
              <Select
                showSearch
                allowClear
                placeholder="选择一份已上传的简历"
                style={{ width: '100%', marginBottom: 16 }}
                optionFilterProp="label"
                value={selectedExistingId ?? undefined}
                onChange={(v) => setSelectedExistingId(typeof v === 'number' ? v : null)}
                options={existingResumes.map((r) => ({
                  value: r.id,
                  label: `${r.original_filename} (#${r.id}) · ${RESUME_STATUS_SHORT[r.status] ?? r.status}`,
                }))}
              />
              <Button
                type="primary"
                size="large"
                onClick={() => void handleUseExistingResume()}
                loading={loading}
                disabled={selectedExistingId == null}
                style={{ width: '100%' }}
              >
                使用该简历
              </Button>
            </Spin>
          )}
        </Card>
      )}

      {currentStep === 1 && (
        <Card style={cardStyle}>
          <Title level={4} style={{ color: 'var(--color-text-primary)' }}>
            第二步：准备优化（目标岗位链接）
          </Title>
          <Paragraph type="secondary">
            请在「目标岗位搜索」中查找并选择岗位，将自动带入链接；也可手动粘贴 Boss直聘等招聘详情页 URL。
          </Paragraph>
          <Paragraph style={{ marginBottom: 16 }}>
            <Link to="/target-jobs">
              <Button type="default" icon={<SearchOutlined />}>
                前往目标岗位搜索
              </Button>
            </Link>
          </Paragraph>

          {resumeErrorMessage ? (
            <Alert
              type="error"
              showIcon
              message="上次优化失败"
              description={resumeErrorMessage}
              style={{ marginBottom: 16 }}
              closable
              onClose={() => setResumeErrorMessage(null)}
            />
          ) : null}

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

      {currentStep === 2 && (
        <Row gutter={[24, 24]}>
          {resumeStatus === 'optimizing' && !loading ? (
            <Col span={24}>
              <Alert
                type="info"
                showIcon
                message="任务进行中"
                description="你可以关闭本页或前往其他菜单；在「历史结果」中点击「继续查看」或带 ?resumeId= 的链接可回到此工作流。下方将自动轮询直至优化完成。"
                style={{ marginBottom: 16 }}
              />
            </Col>
          ) : null}
          <Col xs={24} lg={7}>
            <Card title="LangGraph 节点（点击可查看数据与思考）" style={cardStyle}>
              <Paragraph type="secondary" style={{ marginBottom: 12, fontSize: 12 }}>
                每个节点完成后会推送结构化结果与「分析思路」；生成节点还包含输出片段预览。
              </Paragraph>
              <Timeline items={langGraphTimelineItems} />
              <Divider style={{ margin: '12px 0' }} />
              <Spin spinning={loading} tip={progressText}>
                <Progress percent={progressPercent} status="active" strokeColor="var(--color-primary)" />
              </Spin>
            </Card>
          </Col>
          <Col xs={24} lg={17}>
            <Card title="实时预览（流式输出）" style={cardStyle}>
              <Paragraph type="secondary" style={{ marginBottom: 8 }}>
                {progressText}
              </Paragraph>
              <div
                style={{
                  maxHeight: 'min(70vh, 640px)',
                  overflowY: 'auto',
                  padding: '16px',
                  background: 'var(--color-bg-secondary)',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  minHeight: 200,
                }}
              >
                {optimizedResume ? (
                  <ReactMarkdown components={markdownComponents}>{optimizedResume}</ReactMarkdown>
                ) : (
                  <Text type="secondary">等待模型输出 token…</Text>
                )}
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {currentStep === 3 && (
        <>
        <Row gutter={[24, 24]}>
          {matchAnalysis && (
            <Col xs={24} lg={8}>
              <Card title="匹配分析" style={{ ...cardStyle, height: '100%' }}>
                <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                  <Progress
                    type="circle"
                    percent={matchAnalysis.match_score}
                    strokeColor={{ '0%': 'var(--color-primary)', '100%': 'var(--color-secondary)' }}
                    format={(percent) => (
                      <span style={{ color: 'var(--color-text-primary)', fontSize: '24px' }}>
                        {percent}%
                      </span>
                    )}
                  />
                  <div style={{ marginTop: '8px', color: 'var(--color-text-secondary)' }}>匹配度</div>
                </div>

                <Divider>匹配技能</Divider>
                <div style={{ marginBottom: '16px' }}>
                  {matchAnalysis.matched_skills.map((skill, index) => (
                    <Tag key={index} color="success" style={{ marginBottom: '8px' }}>
                      {skill}
                    </Tag>
                  ))}
                </div>

                <Divider>需补充技能</Divider>
                <div style={{ marginBottom: '16px' }}>
                  {matchAnalysis.missing_skills.map((skill, index) => (
                    <Tag key={index} color="warning" style={{ marginBottom: '8px' }}>
                      {skill}
                    </Tag>
                  ))}
                </div>

                <Divider>优势</Divider>
                <List
                  size="small"
                  dataSource={matchAnalysis.strengths}
                  renderItem={(item) => (
                    <List.Item style={{ borderColor: 'var(--color-border)', padding: '8px 0' }}>
                      <Text type="secondary">✓ {item}</Text>
                    </List.Item>
                  )}
                />

                <Divider>改进建议</Divider>
                <List
                  size="small"
                  dataSource={matchAnalysis.suggestions}
                  renderItem={(item) => (
                    <List.Item style={{ borderColor: 'var(--color-border)', padding: '8px 0' }}>
                      <Text type="secondary">→ {item}</Text>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          )}

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
              style={cardStyle}
            >
              <div
                style={{
                  maxHeight: '600px',
                  overflowY: 'auto',
                  padding: '16px',
                  background: 'var(--color-bg-secondary)',
                  borderRadius: '8px',
                }}
              >
                <ReactMarkdown components={markdownComponents}>{optimizedResume}</ReactMarkdown>
              </div>
            </Card>

            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <Button size="large" onClick={handleReset}>
                优化另一份简历
              </Button>
            </div>
          </Col>
        </Row>

        {resumeStatus === 'optimized' && resumeId != null ? (
          <Row gutter={[24, 24]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card
                title="学习问答（面试准备）"
                style={cardStyle}
                extra={
                  <Button
                    type="primary"
                    loading={studyQaLoading}
                    onClick={() => void handleGenerateStudyQa()}
                  >
                    生成学习问答
                  </Button>
                }
              >
                <Paragraph type="secondary" style={{ marginBottom: 12 }}>
                  根据当前任务的目标岗位、匹配分析与优化稿生成面试准备问题与答题要点；每次点击将重新调用模型生成。
                </Paragraph>
                {studyQaItems.length === 0 ? (
                  <Text type="secondary">尚未生成，点击右上方按钮。</Text>
                ) : (
                  <Collapse
                    items={studyQaItems.map((item, idx) => ({
                      key: String(idx),
                      label: (
                        <span>
                          <Tag color="processing" style={{ marginRight: 8 }}>
                            {item.topic}
                          </Tag>
                          {item.question}
                        </span>
                      ),
                      children: (
                        <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                          {item.answer_hint}
                        </Paragraph>
                      ),
                    }))}
                  />
                )}
              </Card>
            </Col>
          </Row>
        ) : null}

        <Row gutter={[24, 24]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="LangGraph 节点输出（点击可回看）" style={cardStyle}>
              <Paragraph type="secondary" style={{ marginBottom: 12, fontSize: 12 }}>
                此处与优化过程中相同，可再次查看各节点返回的结构化数据与模型分析思路。
              </Paragraph>
              <Timeline items={langGraphTimelineItems} />
            </Card>
          </Col>
        </Row>
        </>
      )}

      <Drawer
        title={
          selectedNodeKey
            ? GRAPH_NODES.find((n) => n.key === selectedNodeKey)?.label ?? '节点详情'
            : '节点详情'
        }
        placement="right"
        width={720}
        open={selectedNodeKey !== null}
        onClose={() => setSelectedNodeKey(null)}
        destroyOnClose
      >
        {!selectedNodeKey ? null : !selectedNodeDetail ? (
          <Paragraph type="secondary">该节点暂无已缓存的输出；请先完成一轮优化流程。</Paragraph>
        ) : (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {selectedNodeDetail.thinking ? (
              <div>
                <Title level={5} style={{ marginTop: 0 }}>
                  分析思路 / 模型思考
                </Title>
                <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{selectedNodeDetail.thinking}</Paragraph>
              </div>
            ) : null}
            {selectedNodeDetail.rawPreview ? (
              <div>
                <Title level={5} style={{ marginTop: 0 }}>
                  模型原始输出片段
                </Title>
                <pre
                  style={{
                    margin: 0,
                    padding: 12,
                    background: 'var(--color-bg-secondary)',
                    borderRadius: 8,
                    fontSize: 12,
                    maxHeight: 240,
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {selectedNodeDetail.rawPreview}
                </pre>
              </div>
            ) : null}
            {selectedNodeDetail.data && Object.keys(selectedNodeDetail.data).length > 0 ? (
              <div>
                <Title level={5} style={{ marginTop: 0 }}>
                  结构化数据
                </Title>
                <pre
                  style={{
                    margin: 0,
                    padding: 12,
                    background: 'var(--color-bg-secondary)',
                    borderRadius: 8,
                    fontSize: 12,
                    maxHeight: '50vh',
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                  }}
                >
                  {JSON.stringify(selectedNodeDetail.data, null, 2)}
                </pre>
              </div>
            ) : (
              <Text type="secondary">暂无结构化数据字段。</Text>
            )}
          </Space>
        )}
      </Drawer>
    </div>
  )
}

export default ResumeOptimizerPage
