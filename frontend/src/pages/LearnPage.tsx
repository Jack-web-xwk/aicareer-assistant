import { useCallback, useEffect, useState, type ReactNode } from 'react'
import {
  Card,
  Row,
  Col,
  Typography,
  List,
  Spin,
  Button,
  Space,
  Tag,
  Empty,
} from 'antd'
import { ReadOutlined, QuestionCircleOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import { Link } from 'react-router-dom'
import { learnApi, resumeApi } from '../services/api'
import type { LearningPhase, LearningArticleDetail, LearningArticleListItem, StudyQaSessionListItem } from '../types'
import type { CSSProperties } from 'react'

const { Title, Paragraph, Text } = Typography

const cardStyle: CSSProperties = {
  background: 'var(--color-bg-primary)',
  border: '1px solid var(--color-border)',
  boxShadow: 'var(--shadow-sm)',
}

const markdownComponents = {
  h1: ({ children }: { children?: ReactNode }) => (
    <Title level={3} style={{ color: 'var(--color-text-primary)', marginTop: 16 }}>{children}</Title>
  ),
  h2: ({ children }: { children?: ReactNode }) => (
    <Title level={4} style={{ color: 'var(--color-text-primary)', marginTop: 12 }}>{children}</Title>
  ),
  h3: ({ children }: { children?: ReactNode }) => (
    <Title level={5} style={{ color: 'var(--color-text-primary)', marginTop: 8 }}>{children}</Title>
  ),
  p: ({ children }: { children?: ReactNode }) => (
    <Paragraph style={{ color: 'var(--color-text-secondary)' }}>{children}</Paragraph>
  ),
  li: ({ children }: { children?: ReactNode }) => (
    <li style={{ color: 'var(--color-text-secondary)' }}>{children}</li>
  ),
  strong: ({ children }: { children?: ReactNode }) => (
    <Text strong style={{ color: 'var(--color-text-primary)' }}>{children}</Text>
  ),
}

function LearnPage() {
  const [phases, setPhases] = useState<LearningPhase[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPhaseId, setSelectedPhaseId] = useState<number | null>(null)
  const [selectedArticle, setSelectedArticle] = useState<LearningArticleDetail | null>(null)
  const [articleLoading, setArticleLoading] = useState(false)
  const [studyQaRecent, setStudyQaRecent] = useState<StudyQaSessionListItem[]>([])

  const loadPhases = useCallback(async () => {
    setLoading(true)
    try {
      const res = await learnApi.phases()
      const data = res.data
      if (res.success && data?.phases && data.phases.length > 0) {
        const phasesData = data.phases
        setPhases(phasesData)
        setSelectedPhaseId((prev) => prev ?? phasesData[0].id)
      } else {
        setPhases([])
      }
    } catch (e) {
      setPhases([])
    } finally {
      setLoading(false)
    }
  }, [])

  const loadStudyQaRecent = useCallback(async () => {
    try {
      const res = await resumeApi.studyQaSessions(0, 3)
      if (res.success && res.data?.items?.length) {
        setStudyQaRecent(res.data.items)
      }
    } catch {
      setStudyQaRecent([])
    }
  }, [])

  useEffect(() => {
    void loadPhases()
  }, [loadPhases])

  useEffect(() => {
    void loadStudyQaRecent()
  }, [loadStudyQaRecent])

  const currentPhase = phases.find((p) => p.id === selectedPhaseId)

  const openArticle = useCallback(async (art: LearningArticleListItem) => {
    setSelectedArticle(null)
    setArticleLoading(true)
    try {
      const res = await learnApi.article(art.id)
      if (res.success && res.data) {
        setSelectedArticle(res.data)
      }
    } finally {
      setArticleLoading(false)
    }
  }, [])

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Space align="center" style={{ marginBottom: 24 }}>
        <ReadOutlined style={{ fontSize: 32, color: 'var(--color-primary)' }} />
        <div>
          <Title level={2} style={{ margin: 0 }}>学无止境</Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            AI 大模型全栈工程师成长专栏 · 从入门到企业级落地
          </Paragraph>
        </div>
      </Space>

      {/* 学习问答入口卡片 */}
      <Card style={{ ...cardStyle, marginBottom: 24 }}>
        <Space align="center" wrap>
          <QuestionCircleOutlined style={{ fontSize: 24, color: '#8b5cf6' }} />
          <div>
            <Text strong>根据简历生成面试准备问答</Text>
            <Paragraph type="secondary" style={{ margin: '4px 0 0', fontSize: 12 }}>
              选择已优化简历，生成面试问答；结果持久化，可在历史中查看。
            </Paragraph>
          </div>
          <Link to="/resume/study-qa">
            <Button type="primary">前往学习问答</Button>
          </Link>
          <Link to="/resume/history">
            <Button>历史结果</Button>
          </Link>
        </Space>
        {studyQaRecent.length > 0 ? (
          <div style={{ marginTop: 12 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>最近记录：</Text>
            {studyQaRecent.map((s) => (
              <Link key={s.id} to="/resume/history" style={{ marginLeft: 8 }}>
                <Tag color="blue">
                  {s.original_filename} · {s.item_count} 条
                </Tag>
              </Link>
            ))}
          </div>
        ) : null}
      </Card>

      <Row gutter={24}>
        {/* 阶段导航 */}
        <Col xs={24} md={8} lg={6}>
          <Card size="small" style={cardStyle} title="学习阶段">
            <Spin spinning={loading}>
              {phases.length === 0 && !loading ? (
                <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              ) : (
                <List
                  size="small"
                  dataSource={phases}
                  renderItem={(p) => (
                    <List.Item
                      style={{
                        cursor: 'pointer',
                        background: selectedPhaseId === p.id ? 'var(--color-primary-bg)' : undefined,
                        borderRadius: 6,
                        padding: '8px 12px',
                      }}
                      onClick={() => {
                        setSelectedPhaseId(p.id)
                        setSelectedArticle(null)
                      }}
                    >
                      <Text
                        ellipsis
                        strong={selectedPhaseId === p.id}
                        style={{ fontSize: 13 }}
                      >
                        {p.subtitle ? `${p.subtitle} · ` : ''}{p.title.slice(0, 20)}…
                      </Text>
                    </List.Item>
                  )}
                />
              )}
            </Spin>
          </Card>
        </Col>

        {/* 主区域：文章列表 或 文章详情 */}
        <Col xs={24} md={16} lg={18}>
          {selectedArticle ? (
            <Card
              style={cardStyle}
              title={
                <Space>
                  <Button
                    type="text"
                    size="small"
                    icon={<ArrowLeftOutlined />}
                    onClick={() => setSelectedArticle(null)}
                  >
                    返回
                  </Button>
                  <span>{selectedArticle.title}</span>
                </Space>
              }
            >
              <Spin spinning={articleLoading}>
                <div
                  style={{
                    maxHeight: '70vh',
                    overflowY: 'auto',
                    padding: 16,
                    background: 'var(--color-bg-secondary)',
                    borderRadius: 8,
                  }}
                >
                  <ReactMarkdown components={markdownComponents}>
                    {selectedArticle.content_md || '_暂无内容_'}
                  </ReactMarkdown>
                </div>
              </Spin>
            </Card>
          ) : (
            <Card
              style={cardStyle}
              title={currentPhase ? currentPhase.title : '选择阶段'}
            >
              {!currentPhase ? (
                <Empty description="请从左侧选择学习阶段" />
              ) : currentPhase.articles.length === 0 ? (
                <Empty description="该阶段暂无文章" />
              ) : (
                <List
                  dataSource={currentPhase.articles}
                  renderItem={(art, idx) => (
                    <List.Item
                      style={{
                        cursor: 'pointer',
                        padding: '12px 0',
                        borderBottom: '1px solid var(--color-border)',
                      }}
                      onClick={() => void openArticle(art)}
                    >
                      <Space>
                        <Tag color="default">{idx + 1}</Tag>
                        <Text>{art.title}</Text>
                        {art.external_url ? (
                          <Tag color="blue">外链</Tag>
                        ) : null}
                      </Space>
                    </List.Item>
                  )}
                />
              )}
            </Card>
          )}
        </Col>
      </Row>
    </div>
  )
}

export default LearnPage
