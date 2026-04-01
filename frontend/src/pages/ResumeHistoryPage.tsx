import { useEffect, useState, useMemo, type ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Card,
  Typography,
  Table,
  Button,
  Space,
  Drawer,
  Tag,
  message,
  Spin,
  Popconfirm,
  Empty,
  Tabs,
  List,
  Divider,
  Descriptions,
  Tooltip,
  Collapse,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  HistoryOutlined,
  EyeOutlined,
  DownloadOutlined,
  ReloadOutlined,
  AudioOutlined,
  DeleteOutlined,
  UnlockOutlined,
  RedoOutlined,
  ReadOutlined,
} from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Link } from 'react-router-dom'
import { resumeApi, interviewApi } from '../services/api'
import type {
  ResumeHistoryListItem,
  ResumeInfo,
  InterviewHistoryListItem,
  InterviewReport,
  ResumeStatus,
  StudyQaSessionListItem,
  StudyQaSessionDetail,
} from '../types'

const { Title, Paragraph, Text } = Typography

const PAGE_SIZE = 10

const RESUME_TASK_STATUS: Record<
  ResumeStatus,
  { color: string; text: string }
> = {
  uploaded: { color: 'default', text: '已上传' },
  parsing: { color: 'processing', text: '解析中' },
  parsed: { color: 'blue', text: '待优化' },
  optimizing: { color: 'processing', text: '优化中' },
  optimized: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
}

type HistoryTab = 'resume' | 'interview' | 'studyQa'

function ResumeHistoryPage() {
  const [searchParams] = useSearchParams()
  const urlTab = searchParams.get('tab') as HistoryTab | null
  const [tab, setTab] = useState<HistoryTab>(urlTab || 'resume')

  const [resumeLoading, setResumeLoading] = useState(true)
  const [resumeItems, setResumeItems] = useState<ResumeHistoryListItem[]>([])
  const [resumeTotal, setResumeTotal] = useState(0)
  const [resumePage, setResumePage] = useState(1)

  const [interviewLoading, setInterviewLoading] = useState(false)
  const [interviewItems, setInterviewItems] = useState<InterviewHistoryListItem[]>([])
  const [interviewTotal, setInterviewTotal] = useState(0)
  const [interviewPage, setInterviewPage] = useState(1)

  const [studyQaLoading, setStudyQaLoading] = useState(false)
  const [studyQaItems, setStudyQaItems] = useState<StudyQaSessionListItem[]>([])
  const [studyQaTotal, setStudyQaTotal] = useState(0)
  const [studyQaPage, setStudyQaPage] = useState(1)

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [drawerKind, setDrawerKind] = useState<'resume' | 'interview' | 'studyQa' | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [resumeDetail, setResumeDetail] = useState<ResumeInfo | null>(null)
  const [interviewReport, setInterviewReport] = useState<InterviewReport | null>(null)
  const [studyQaDetail, setStudyQaDetail] = useState<StudyQaSessionDetail | null>(null)

  const handleUnlockResume = async (id: number) => {
    try {
      const res = await resumeApi.unlockOptimization(id)
      if (res.success) {
        message.success('已解除「优化中」状态，可在简历优化页重新发起流式优化')
        void loadResumeHistory((resumePage - 1) * PAGE_SIZE, PAGE_SIZE)
      } else {
        message.error(res.message || '操作失败')
      }
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const handleDeleteResumeRecord = async (id: number) => {
    try {
      const res = await resumeApi.delete(id)
      if (res.success) {
        message.success('已删除')
        void loadResumeHistory((resumePage - 1) * PAGE_SIZE, PAGE_SIZE)
      } else {
        message.error(res.message || '删除失败')
      }
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const loadResumeHistory = async (skip: number, limit: number) => {
    setResumeLoading(true)
    try {
      const res = await resumeApi.history(skip, limit)
      if (res.success && res.data) {
        setResumeItems(Array.isArray(res.data.items) ? res.data.items : [])
        setResumeTotal(typeof res.data.total === 'number' ? res.data.total : 0)
      } else {
        setResumeItems([])
        setResumeTotal(0)
        if (!res.success) {
          message.warning(res.message || '简历历史接口返回异常')
        }
      }
    } catch (e) {
      message.error(`加载简历历史失败: ${(e as Error).message}`)
    } finally {
      setResumeLoading(false)
    }
  }

  const loadInterviewHistory = async (skip: number, limit: number) => {
    setInterviewLoading(true)
    try {
      const res = await interviewApi.history(skip, limit)
      if (res.success && res.data) {
        setInterviewItems(Array.isArray(res.data.items) ? res.data.items : [])
        setInterviewTotal(typeof res.data.total === 'number' ? res.data.total : 0)
      } else {
        setInterviewItems([])
        setInterviewTotal(0)
        if (!res.success) {
          message.warning(res.message || '面试历史接口返回异常')
        }
      }
    } catch (e) {
      message.error(`加载面试历史失败: ${(e as Error).message}`)
    } finally {
      setInterviewLoading(false)
    }
  }

  const loadStudyQaHistory = async (skip: number, limit: number) => {
    setStudyQaLoading(true)
    try {
      const res = await resumeApi.studyQaSessions(skip, limit)
      if (res.success && res.data) {
        setStudyQaItems(Array.isArray(res.data.items) ? res.data.items : [])
        setStudyQaTotal(typeof res.data.total === 'number' ? res.data.total : 0)
      } else {
        setStudyQaItems([])
        setStudyQaTotal(0)
        if (!res.success) {
          message.warning(res.message || '学习问答列表接口异常')
        }
      }
    } catch (e) {
      message.error(`加载学习问答记录失败: ${(e as Error).message}`)
    } finally {
      setStudyQaLoading(false)
    }
  }

  useEffect(() => {
    void loadResumeHistory((resumePage - 1) * PAGE_SIZE, PAGE_SIZE)
  }, [resumePage])

  useEffect(() => {
    if (tab !== 'interview') return
    void loadInterviewHistory((interviewPage - 1) * PAGE_SIZE, PAGE_SIZE)
  }, [tab, interviewPage])

  useEffect(() => {
    if (tab !== 'studyQa') return
    void loadStudyQaHistory((studyQaPage - 1) * PAGE_SIZE, PAGE_SIZE)
  }, [tab, studyQaPage])

  const openResumeDetail = async (id: number) => {
    setDrawerKind('resume')
    setDrawerOpen(true)
    setResumeDetail(null)
    setInterviewReport(null)
    setStudyQaDetail(null)
    setDetailLoading(true)
    try {
      const res = await resumeApi.get(id)
      if (res.success && res.data) {
        setResumeDetail(res.data)
      }
    } catch (e) {
      message.error(`加载详情失败: ${(e as Error).message}`)
      setDrawerOpen(false)
      setDrawerKind(null)
    } finally {
      setDetailLoading(false)
    }
  }

  const openStudyQaDetail = async (sessionId: number) => {
    setDrawerKind('studyQa')
    setDrawerOpen(true)
    setResumeDetail(null)
    setInterviewReport(null)
    setStudyQaDetail(null)
    setDetailLoading(true)
    try {
      const res = await resumeApi.studyQaSessionGet(sessionId)
      if (res.success && res.data) {
        setStudyQaDetail(res.data)
      }
    } catch (e) {
      message.error(`加载学习问答详情失败: ${(e as Error).message}`)
      setDrawerOpen(false)
      setDrawerKind(null)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleDeleteStudyQa = async (sessionId: number) => {
    try {
      const res = await resumeApi.studyQaSessionDelete(sessionId)
      if (res.success) {
        message.success('已删除')
        setDrawerOpen(false)
        setDrawerKind(null)
        setStudyQaDetail(null)
        void loadStudyQaHistory((studyQaPage - 1) * PAGE_SIZE, PAGE_SIZE)
      } else {
        message.error(res.message || '删除失败')
      }
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const openInterviewDetail = async (sessionId: string) => {
    setDrawerKind('interview')
    setDrawerOpen(true)
    setResumeDetail(null)
    setInterviewReport(null)
    setStudyQaDetail(null)
    setDetailLoading(true)
    try {
      const res = await interviewApi.getReport(sessionId)
      if (res.success && res.data) {
        setInterviewReport(res.data)
      }
    } catch (e) {
      message.error(`加载面试报告失败: ${(e as Error).message}`)
      setDrawerOpen(false)
      setDrawerKind(null)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleDownloadResume = async (id: number) => {
    try {
      const content = await resumeApi.download(id, 'md')
      const blob = new Blob([content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `optimized_resume_${id}.md`
      a.click()
      URL.revokeObjectURL(url)
      message.success('已开始下载')
    } catch (e) {
      message.error(`下载失败: ${(e as Error).message}`)
    }
  }

  const handleDownloadInterviewMd = () => {
    if (!interviewReport?.detailed_report) {
      message.warning('暂无报告正文')
      return
    }
    const blob = new Blob([interviewReport.detailed_report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `interview_report_${interviewReport.session_id}.md`
    a.click()
    URL.revokeObjectURL(url)
    message.success('已开始下载')
  }

  const mdComponents = useMemo(
    () => ({
      h1: ({ children }: { children?: ReactNode }) => (
        <Title level={3} style={{ color: 'var(--color-text-primary)' }}>
          {children}
        </Title>
      ),
      h2: ({ children }: { children?: ReactNode }) => (
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
    }),
    []
  )

  const resumeColumns: ColumnsType<ResumeHistoryListItem> = [
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      fixed: 'left',
      render: (s: ResumeStatus) => {
        const cfg = RESUME_TASK_STATUS[s] ?? { color: 'default', text: s }
        return <Tag color={cfg.color}>{cfg.text}</Tag>
      },
    },
    {
      title: '简历文件',
      dataIndex: 'original_filename',
      key: 'original_filename',
      ellipsis: true,
      width: 160,
      render: (text: string, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            #{record.id} · {record.file_type}
          </Text>
        </Space>
      ),
    },
    {
      title: '目标岗位 / 链接',
      key: 'job_title_url',
      ellipsis: true,
      width: 220,
      render: (_, record) => {
        const title =
          record.job_snapshot?.title || record.target_job_title || '—'
        const url = record.job_snapshot?.source_url || record.target_job_url
        return (
          <Space direction="vertical" size={0}>
            <Text strong>{title}</Text>
            {url ? (
              <Tooltip title={url}>
                <a href={url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                  打开岗位页
                </a>
              </Tooltip>
            ) : null}
          </Space>
        )
      },
    },
    {
      title: '公司',
      key: 'company',
      width: 120,
      ellipsis: true,
      render: (_, record) =>
        record.job_snapshot?.company ? (
          <Text>{record.job_snapshot.company}</Text>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: '薪资',
      key: 'salary',
      width: 110,
      render: (_, record) =>
        record.job_snapshot?.salary ? (
          <Tag color="orange">{record.job_snapshot.salary}</Tag>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: '地点',
      key: 'location',
      width: 100,
      ellipsis: true,
      render: (_, record) =>
        record.job_snapshot?.location ? (
          <Text ellipsis>{record.job_snapshot.location}</Text>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: '技能/要求要点',
      key: 'skills',
      ellipsis: true,
      render: (_, record) => {
        const skills = record.job_snapshot?.required_skills?.slice(0, 10) ?? []
        if (!skills.length) {
          return <Text type="secondary">—</Text>
        }
        return (
          <Space size={[4, 4]} wrap>
            {skills.map((s) => (
              <Tag key={s}>{s}</Tag>
            ))}
          </Space>
        )
      },
    },
    {
      title: '匹配度',
      dataIndex: 'match_score',
      key: 'match_score',
      width: 90,
      render: (s: number | null | undefined) =>
        s != null ? <Tag color="blue">{s}%</Tag> : <Text type="secondary">—</Text>,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 170,
      render: (t: string) => new Date(t).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      width: 400,
      fixed: 'right',
      render: (_, record) => (
        <Space wrap size="small">
          {record.status === 'optimizing' ? (
            <>
              <Link to={`/resume?resumeId=${record.id}`}>
                <Button type="primary" size="small" icon={<EyeOutlined />}>
                  继续任务
                </Button>
              </Link>
              <Popconfirm
                title="解除「优化中」？"
                description="若页面已关闭导致 SSE 中断，可解除后回到优化页重新发起。"
                onConfirm={() => void handleUnlockResume(record.id)}
              >
                <Button size="small" icon={<UnlockOutlined />}>
                  解除卡住
                </Button>
              </Popconfirm>
            </>
          ) : null}
          {record.status === 'parsed' ||
          record.status === 'uploaded' ||
          record.status === 'parsing' ? (
            <Link to={`/resume?resumeId=${record.id}`}>
              <Button type="primary" size="small">
                继续
              </Button>
            </Link>
          ) : null}
          {record.status === 'failed' ? (
            <>
              <Link to={`/resume?resumeId=${record.id}`}>
                <Button type="link" size="small">
                  查看原因
                </Button>
              </Link>
              <Link to={`/resume?resumeId=${record.id}`}>
                <Button size="small" icon={<RedoOutlined />}>
                  重新优化
                </Button>
              </Link>
            </>
          ) : null}
          {record.status === 'optimized' ? (
            <>
              <Link to={`/resume?resumeId=${record.id}`}>
                <Button type="primary" size="small" icon={<EyeOutlined />}>
                  查看结果
                </Button>
              </Link>
              <Tooltip title="在侧栏快速预览匹配分析与优化稿，不跳转页面">
                <Button
                  type="link"
                  size="small"
                  icon={<EyeOutlined />}
                  onClick={() => openResumeDetail(record.id)}
                >
                  侧栏预览
                </Button>
              </Tooltip>
              <Button
                type="link"
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => handleDownloadResume(record.id)}
              >
                下载
              </Button>
              <Tooltip title="使用该岗位信息开始模拟面试">
                <Link to={`/interview?resumeId=${record.id}&jobUrl=${encodeURIComponent(record.target_job_url || '')}`}>
                  <Button type="link" size="small" icon={<AudioOutlined />}>
                    模拟面试
                  </Button>
                </Link>
              </Tooltip>
              <Tooltip title="基于匹配度差距生成专项学习">
                <Link to={`/learn?resumeId=${record.id}&type=resume-gap`}>
                  <Button type="link" size="small" icon={<ReadOutlined />}>
                    专项学习
                  </Button>
                </Link>
              </Tooltip>
            </>
          ) : null}
          <Popconfirm
            title="确定删除？"
            description="将删除数据库记录及已上传文件，不可恢复。"
            onConfirm={() => void handleDeleteResumeRecord(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const interviewColumns: ColumnsType<InterviewHistoryListItem> = [
    {
      title: '目标岗位',
      dataIndex: 'job_role',
      key: 'job_role',
      ellipsis: true,
      render: (text: string, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }} ellipsis>
            {record.session_id}
          </Text>
        </Space>
      ),
    },
    {
      title: '技术栈',
      dataIndex: 'tech_stack',
      key: 'tech_stack',
      ellipsis: true,
      render: (stacks: string[]) =>
        stacks?.length ? (
          <Space size={[4, 4]} wrap>
            {stacks.slice(0, 6).map((s) => (
              <Tag key={s}>{s}</Tag>
            ))}
            {stacks.length > 6 ? <Tag>+{stacks.length - 6}</Tag> : null}
          </Space>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: '得分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 90,
      render: (s: number | null) =>
        s != null ? <Tag color="green">{s}</Tag> : <Text type="secondary">—</Text>,
    },
    {
      title: '时长',
      dataIndex: 'duration_minutes',
      key: 'duration_minutes',
      width: 90,
      render: (m: number | null) =>
        m != null ? <Text>{m} 分钟</Text> : <Text type="secondary">—</Text>,
    },
    {
      title: '完成时间',
      dataIndex: 'ended_at',
      key: 'ended_at',
      width: 200,
      render: (t: string | null) => (t ? new Date(t).toLocaleString() : '—'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space wrap size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => openInterviewDetail(record.session_id)}
          >
            查看报告
          </Button>
          <Tooltip title="针对薄弱环节专项学习">
            <Link to={`/learn?sessionId=${record.session_id}&type=interview-weakness`}>
              <Button type="link" size="small" icon={<ReadOutlined />}>
                专项学习
              </Button>
            </Link>
          </Tooltip>
          <Tooltip title="使用相同配置重新挑战">
            <Link to={`/interview?sessionId=${record.session_id}&action=replay`}>
              <Button type="link" size="small" icon={<RedoOutlined />}>
                重新挑战
              </Button>
            </Link>
          </Tooltip>
        </Space>
      ),
    },
  ]

  const studyQaColumns: ColumnsType<StudyQaSessionListItem> = [
    {
      title: '生成时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (t: string) => new Date(t).toLocaleString(),
    },
    {
      title: '简历文件',
      dataIndex: 'original_filename',
      key: 'original_filename',
      ellipsis: true,
      render: (text: string, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            简历 #{record.resume_id} · 会话 #{record.id}
          </Text>
        </Space>
      ),
    },
    {
      title: '目标岗位',
      dataIndex: 'target_job_title',
      key: 'target_job_title',
      ellipsis: true,
      render: (t: string | null | undefined) => t || <Text type="secondary">—</Text>,
    },
    {
      title: '条数',
      dataIndex: 'item_count',
      key: 'item_count',
      width: 72,
      render: (n: number) => <Tag color="blue">{n}</Tag>,
    },
    {
      title: '预览',
      dataIndex: 'preview',
      key: 'preview',
      ellipsis: true,
      render: (p: string | null | undefined) =>
        p ? <Text type="secondary">{p}</Text> : <Text type="secondary">—</Text>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => void openStudyQaDetail(record.id)}
          >
            详情
          </Button>
          <Tooltip title="深入学习相关知识点">
            <Link to={`/learn?qaId=${record.id}&type=qa-deep-learn`}>
              <Button type="link" size="small" icon={<ReadOutlined />}>
                深入学习
              </Button>
            </Link>
          </Tooltip>
          <Popconfirm
            title="删除此条学习问答记录？"
            onConfirm={() => void handleDeleteStudyQa(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const refreshCurrent = () => {
    if (tab === 'resume') {
      void loadResumeHistory((resumePage - 1) * PAGE_SIZE, PAGE_SIZE)
    } else if (tab === 'interview') {
      void loadInterviewHistory((interviewPage - 1) * PAGE_SIZE, PAGE_SIZE)
    } else {
      void loadStudyQaHistory((studyQaPage - 1) * PAGE_SIZE, PAGE_SIZE)
    }
  }

  return (
    <div className="fade-in">
      <Space align="center" style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Title level={2} style={{ margin: 0, color: 'var(--color-text-primary)' }}>
          <HistoryOutlined style={{ marginRight: 12, color: 'var(--color-primary)' }} />
          历史与任务
        </Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => void refreshCurrent()}>
            刷新
          </Button>
          <Link to="/target-jobs">
            <Button>目标岗位</Button>
          </Link>
          <Link to="/resume">
            <Button>简历优化</Button>
          </Link>
          <Link to="/resume/study-qa">
            <Button>学习问答</Button>
          </Link>
          <Link to="/interview">
            <Button type="primary" icon={<AudioOutlined />}>
              面试模拟
            </Button>
          </Link>
        </Space>
      </Space>

      <Paragraph type="secondary" style={{ marginBottom: 16 }}>
        <strong>简历任务</strong>：汇总上传、解析、待优化、优化中、已完成、失败等全部记录（原「上传记录」已合并至此）。
        优化中可「继续任务」打开工作流；若页面关闭导致中断，可用「解除卡住」后重新发起。
        <strong>面试模拟</strong>：查看历史评估报告。
        <strong>学习问答</strong>：每次「生成学习问答」的持久化记录，可查看详情或删除。
      </Paragraph>

      <Card
        style={{
          background: 'var(--color-bg-primary)',
          border: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        <Tabs
          activeKey={tab}
          onChange={(k) => {
            const next = k as HistoryTab
            setTab(next)
            if (next === 'interview') {
              setInterviewLoading(true)
            }
            if (next === 'studyQa') {
              setStudyQaLoading(true)
            }
          }}
          items={[
            {
              key: 'resume',
              label: '简历任务',
              children: (
                <Spin spinning={resumeLoading}>
                  {resumeItems.length === 0 && !resumeLoading ? (
                    <Empty description="暂无简历记录" />
                  ) : (
                    <Table<ResumeHistoryListItem>
                      rowKey="id"
                      columns={resumeColumns}
                      dataSource={resumeItems}
                      scroll={{ x: 1480 }}
                      pagination={{
                        current: resumePage,
                        pageSize: PAGE_SIZE,
                        total: resumeTotal,
                        showTotal: (t) => `共 ${t} 条`,
                        onChange: (p) => setResumePage(p),
                      }}
                      size="middle"
                    />
                  )}
                </Spin>
              ),
            },
            {
              key: 'interview',
              label: '面试模拟',
              children: (
                <Spin spinning={interviewLoading}>
                  {interviewItems.length === 0 && !interviewLoading ? (
                    <Empty description="暂无已完成的模拟面试，完成一场面试后将显示在此" />
                  ) : (
                    <Table<InterviewHistoryListItem>
                      rowKey="session_id"
                      columns={interviewColumns}
                      dataSource={interviewItems}
                      pagination={{
                        current: interviewPage,
                        pageSize: PAGE_SIZE,
                        total: interviewTotal,
                        showTotal: (t) => `共 ${t} 条`,
                        onChange: (p) => setInterviewPage(p),
                      }}
                      size="middle"
                    />
                  )}
                </Spin>
              ),
            },
            {
              key: 'studyQa',
              label: '学习问答',
              children: (
                <Spin spinning={studyQaLoading}>
                  {studyQaItems.length === 0 && !studyQaLoading ? (
                    <Empty description="暂无学习问答记录，请在「学习问答」页或简历优化结果中生成" />
                  ) : (
                    <Table<StudyQaSessionListItem>
                      rowKey="id"
                      columns={studyQaColumns}
                      dataSource={studyQaItems}
                      scroll={{ x: 960 }}
                      pagination={{
                        current: studyQaPage,
                        pageSize: PAGE_SIZE,
                        total: studyQaTotal,
                        showTotal: (t) => `共 ${t} 条`,
                        onChange: (p) => setStudyQaPage(p),
                      }}
                      size="middle"
                    />
                  )}
                </Spin>
              ),
            },
          ]}
        />
      </Card>

      <Drawer
        title={
          drawerKind === 'resume' && resumeDetail
            ? `优化结果 · ${resumeDetail.original_filename}`
            : drawerKind === 'interview' && interviewReport
              ? `面试报告 · ${interviewReport.job_role}`
              : drawerKind === 'studyQa' && studyQaDetail
                ? `学习问答 · ${studyQaDetail.original_filename}`
                : '加载中…'
        }
        placement="right"
        width={720}
        onClose={() => {
          setDrawerOpen(false)
          setDrawerKind(null)
          setResumeDetail(null)
          setInterviewReport(null)
          setStudyQaDetail(null)
        }}
        open={drawerOpen}
        extra={
          drawerKind === 'resume' && resumeDetail ? (
            <Button type="primary" icon={<DownloadOutlined />} onClick={() => handleDownloadResume(resumeDetail.id)}>
              下载 Markdown
            </Button>
          ) : drawerKind === 'interview' && interviewReport?.detailed_report ? (
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleDownloadInterviewMd}>
              下载报告 Markdown
            </Button>
          ) : drawerKind === 'studyQa' && studyQaDetail ? (
            <Popconfirm title="删除此条记录？" onConfirm={() => void handleDeleteStudyQa(studyQaDetail.id)}>
              <Button danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          ) : null
        }
      >
        <Spin spinning={detailLoading}>
          {drawerKind === 'resume' && resumeDetail && (
            <>
              <Card size="small" style={{ marginBottom: 16 }} title="应聘岗位信息（爬取快照）">
                {resumeDetail.job_snapshot?.scrape_error ? (
                  <Paragraph style={{ marginBottom: 12 }}>
                    <Text type="warning">
                      岗位页解析未完全成功：{resumeDetail.job_snapshot.scrape_error}
                    </Text>
                  </Paragraph>
                ) : null}
                <Descriptions column={1} size="small" labelStyle={{ width: 120 }}>
                  <Descriptions.Item label="岗位名称">
                    {resumeDetail.job_snapshot?.title || resumeDetail.target_job_title || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="公司名称">
                    {resumeDetail.job_snapshot?.company || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="薪资">
                    {resumeDetail.job_snapshot?.salary || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="工作地点">
                    {resumeDetail.job_snapshot?.location || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="经验 / 学历">
                    {resumeDetail.job_snapshot?.experience_years || '—'} ·{' '}
                    {resumeDetail.job_snapshot?.education_requirement || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="行业 / 规模 / 融资">
                    {[resumeDetail.job_snapshot?.industry, resumeDetail.job_snapshot?.company_scale, resumeDetail.job_snapshot?.financing_stage]
                      .filter(Boolean)
                      .join(' · ') || '—'}
                  </Descriptions.Item>
                  <Descriptions.Item label="岗位链接">
                    {(resumeDetail.job_snapshot?.source_url || resumeDetail.target_job_url) ? (
                      <a
                        href={resumeDetail.job_snapshot?.source_url || resumeDetail.target_job_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {resumeDetail.job_snapshot?.source_url || resumeDetail.target_job_url}
                      </a>
                    ) : (
                      '—'
                    )}
                  </Descriptions.Item>
                </Descriptions>
                {resumeDetail.job_snapshot?.required_skills?.length ? (
                  <>
                    <Divider orientation="left" plain style={{ margin: '12px 0 8px' }}>
                      技能与任职要求
                    </Divider>
                    <Space size={[6, 6]} wrap>
                      {resumeDetail.job_snapshot.required_skills.map((s) => (
                        <Tag key={s}>{s}</Tag>
                      ))}
                    </Space>
                  </>
                ) : null}
              </Card>
              <div
                style={{
                  maxHeight: '70vh',
                  overflowY: 'auto',
                  padding: 16,
                  background: 'var(--color-bg-secondary)',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                }}
              >
                <ReactMarkdown components={mdComponents}>
                  {resumeDetail.optimized_resume || '_无内容_'}
                </ReactMarkdown>
              </div>
            </>
          )}

          {drawerKind === 'interview' && interviewReport && (
            <>
              <Space wrap style={{ marginBottom: 16 }}>
                <Tag color="blue">总分 {interviewReport.total_score ?? '—'}</Tag>
                {interviewReport.duration_minutes != null && (
                  <Tag>时长 {interviewReport.duration_minutes} 分钟</Tag>
                )}
                {interviewReport.tech_stack?.map((s) => (
                  <Tag key={s}>{s}</Tag>
                ))}
              </Space>
              {interviewReport.strengths?.length ? (
                <>
                  <Text strong>优势</Text>
                  <List
                    size="small"
                    dataSource={interviewReport.strengths}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                </>
              ) : null}
              {interviewReport.weaknesses?.length ? (
                <>
                  <Text strong>待提升</Text>
                  <List
                    size="small"
                    dataSource={interviewReport.weaknesses}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                </>
              ) : null}
              {interviewReport.suggestions?.length ? (
                <>
                  <Text strong>建议</Text>
                  <List
                    size="small"
                    dataSource={interviewReport.suggestions}
                    renderItem={(item) => <List.Item>{item}</List.Item>}
                  />
                </>
              ) : null}
              <Divider />
              <div
                style={{
                  maxHeight: '50vh',
                  overflowY: 'auto',
                  padding: 16,
                  background: 'var(--color-bg-secondary)',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                }}
              >
                <ReactMarkdown components={mdComponents}>
                  {interviewReport.detailed_report || '_暂无详细报告_'}
                </ReactMarkdown>
              </div>
            </>
          )}

          {drawerKind === 'studyQa' && studyQaDetail && (
            <>
              <Descriptions column={1} size="small" style={{ marginBottom: 16 }} bordered>
                <Descriptions.Item label="会话 ID">{studyQaDetail.id}</Descriptions.Item>
                <Descriptions.Item label="简历 ID">{studyQaDetail.resume_id}</Descriptions.Item>
                <Descriptions.Item label="文件名">{studyQaDetail.original_filename}</Descriptions.Item>
                <Descriptions.Item label="目标岗位">
                  {studyQaDetail.target_job_title || '—'}
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag>{studyQaDetail.status}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="生成时间">
                  {new Date(studyQaDetail.created_at).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="条数">{studyQaDetail.item_count}</Descriptions.Item>
                {studyQaDetail.target_job_url ? (
                  <Descriptions.Item label="岗位链接">
                    <a href={studyQaDetail.target_job_url} target="_blank" rel="noreferrer">
                      {studyQaDetail.target_job_url}
                    </a>
                  </Descriptions.Item>
                ) : null}
              </Descriptions>
              <Collapse
                items={studyQaDetail.items.map((item, idx) => ({
                  key: String(idx),
                  label: `${idx + 1}. ${item.topic} · ${item.question.length > 72 ? `${item.question.slice(0, 72)}…` : item.question}`,
                  children: (
                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                      <div>
                        <Text strong>问题</Text>
                        <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>{item.question}</Paragraph>
                      </div>
                      <div>
                        <Text strong>答题要点</Text>
                        <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>{item.answer_hint}</Paragraph>
                      </div>
                    </Space>
                  ),
                }))}
              />
            </>
          )}
        </Spin>
      </Drawer>
    </div>
  )
}

export default ResumeHistoryPage
