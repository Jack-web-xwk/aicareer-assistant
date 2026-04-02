import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Card,
  Drawer,
  Grid,
  Col,
  Row,
  Typography,
  List,
  Spin,
  Empty,
  Alert,
  Segmented,
  Tag,
  Space,
  Collapse,
  Button,
} from 'antd'
import { RocketOutlined, ExperimentOutlined, MenuOutlined } from '@ant-design/icons'
import { LearningMarkdown } from '../../components/LearningMarkdown'
import type { AiDailyCatalog, AiDailyCatalogEntry, AiDailyCategoryKey } from '../../types'
import type { CSSProperties } from 'react'

const { Paragraph, Text } = Typography

const cardStyle: CSSProperties = {
  background: 'var(--color-bg-primary)',
  border: '1px solid var(--color-border)',
  boxShadow: 'var(--shadow-sm)',
}

function catalogUrl(): string {
  const base = import.meta.env.BASE_URL
  const prefix = base.endsWith('/') ? base : `${base}/`
  return `${prefix}ai-daily/catalog.json`
}

function markdownAssetUrl(relpath: string): string {
  const base = import.meta.env.BASE_URL
  const prefix = base.endsWith('/') ? base : `${base}/`
  const encoded = relpath
    .split('/')
    .map((seg) => encodeURIComponent(seg))
    .join('/')
  return `${prefix}ai-daily/${encoded}`
}

const TOP_LABELS: Record<AiDailyCategoryKey, string> = {
  daily: '日报',
  weekly: '周报',
  apps: '应用实战',
}

export default function AiFrontierLearning() {
  const [catalog, setCatalog] = useState<AiDailyCatalog | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [topKey, setTopKey] = useState<AiDailyCategoryKey>('daily')
  const [selected, setSelected] = useState<AiDailyCatalogEntry | null>(null)
  const [mdContent, setMdContent] = useState<string>('')
  const [mdLoading, setMdLoading] = useState(false)

  const [browseDrawerOpen, setBrowseDrawerOpen] = useState(false)
  const screens = Grid.useBreakpoint()
  const isLgUp = Boolean(screens.lg)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setLoadError(null)
    void fetch(catalogUrl())
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<AiDailyCatalog>
      })
      .then((data) => {
        if (!cancelled) setCatalog(data)
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setLoadError(e instanceof Error ? e.message : '加载目录失败')
          setCatalog(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!catalog?.entries.length) {
      setSelected(null)
      return
    }
    const first = catalog.entries.find((e) => e.category === topKey)
    setSelected(first ?? null)
  }, [topKey, catalog])

  const loadMd = useCallback(async (entry: AiDailyCatalogEntry | null) => {
    if (!entry) {
      setMdContent('')
      return
    }
    setMdLoading(true)
    try {
      const r = await fetch(markdownAssetUrl(entry.relpath))
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const text = await r.text()
      setMdContent(text)
    } catch {
      setMdContent('_加载正文失败，请稍后重试。_')
    } finally {
      setMdLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadMd(selected)
  }, [selected, loadMd])

  const sectionGroups = useMemo(() => {
    if (!catalog) return new Map<string, AiDailyCatalogEntry[]>()
    const filtered = catalog.entries.filter((e) => e.category === topKey)
    const map = new Map<string, AiDailyCatalogEntry[]>()
    for (const e of filtered) {
      const list = map.get(e.section) ?? []
      list.push(e)
      map.set(e.section, list)
    }
    return map
  }, [catalog, topKey])

  const browseBody = (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Segmented<AiDailyCategoryKey>
        block
        value={topKey}
        onChange={(v) => setTopKey(v as AiDailyCategoryKey)}
        options={[
          { label: TOP_LABELS.daily, value: 'daily' },
          { label: TOP_LABELS.weekly, value: 'weekly' },
          { label: TOP_LABELS.apps, value: 'apps' },
        ]}
      />
      <Spin spinning={loading}>
        {sectionGroups.size === 0 && !loading ? (
          <Empty description="该分类暂无条目" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <Collapse
            bordered={false}
            defaultActiveKey={Array.from(sectionGroups.keys()).slice(0, 3)}
            items={Array.from(sectionGroups.entries()).map(([section, items]) => ({
              key: section,
              label: (
                <Text strong style={{ fontSize: 13 }}>
                  {section}
                  <Tag style={{ marginLeft: 8 }}>{items.length}</Tag>
                </Text>
              ),
              children: (
                <List
                  size="small"
                  dataSource={items}
                  renderItem={(item) => (
                    <List.Item
                      style={{
                        cursor: 'pointer',
                        padding: '6px 8px',
                        borderRadius: 6,
                        background:
                          selected?.relpath === item.relpath ? 'var(--color-primary-bg)' : undefined,
                      }}
                      onClick={() => {
                        setSelected(item)
                        setBrowseDrawerOpen(false)
                      }}
                    >
                      <div style={{ width: '100%' }}>
                        <Text ellipsis style={{ display: 'block', fontSize: 13 }}>
                          {item.title}
                        </Text>
                        {item.sortDate ? (
                          <Tag color="blue" style={{ marginTop: 4 }}>
                            {item.sortDate}
                          </Tag>
                        ) : null}
                      </div>
                    </List.Item>
                  )}
                />
              ),
            }))}
          />
        )}
      </Spin>
    </Space>
  )

  return (
    <div>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="内容来源与说明"
        description={
          <Paragraph style={{ marginBottom: 0, fontSize: 13 }}>
            正文来自 Gitee 开源仓库{' '}
            <Text code>xia-weikun/ai-daily</Text>（
            <a href="https://gitee.com/xia-weikun/ai-daily" target="_blank" rel="noreferrer">
              链接
            </a>
            ），由自动化流程聚合生成，仅供学习参考，不构成投资或技术决策建议。
          </Paragraph>
        }
      />

      <Card
        style={{
          ...cardStyle,
          marginBottom: 16,
          background: 'linear-gradient(135deg, var(--color-bg-secondary) 0%, var(--color-bg-primary) 100%)',
        }}
        styles={{ body: { padding: '20px 24px' } }}
      >
        <Space align="start" size="large" wrap>
          <ExperimentOutlined style={{ fontSize: 36, color: 'var(--color-secondary)' }} />
          <div>
            <Typography.Title level={4} style={{ margin: 0 }}>
              AI 前沿技术学习
            </Typography.Title>
            <Paragraph type="secondary" style={{ marginBottom: 0, maxWidth: 560 }}>
              每日 / 每周精选与实战应用，与「学无止境」专栏互补，聚焦产业与论文动态。
            </Paragraph>
          </div>
          <RocketOutlined style={{ fontSize: 28, color: 'var(--color-primary)', opacity: 0.85 }} />
        </Space>
      </Card>

      {loadError ? (
        <Alert type="error" message={loadError} description="请确认已执行构建期同步脚本并存在 ai-daily/catalog.json。" />
      ) : null}

      <Row gutter={[16, 16]}>
        {isLgUp ? (
          <Col xs={24} lg={6} xl={5}>
            <Card size="small" style={cardStyle} title="浏览">
              {browseBody}
            </Card>
          </Col>
        ) : null}

        <Col xs={24} lg={18} xl={19}>
          <Card
            style={cardStyle}
            title={
              <Space>
                {!isLgUp ? (
                  <Button
                    type="text"
                    size="small"
                    icon={<MenuOutlined />}
                    onClick={() => setBrowseDrawerOpen(true)}
                  >
                    目录
                  </Button>
                ) : null}
                <span>{selected ? selected.title : '请选择文章'}</span>
              </Space>
            }
            styles={{ body: { padding: 0 } }}
          >
            <Spin spinning={mdLoading}>
              <div
                style={{
                  maxHeight: 'calc(100vh - 300px)',
                  padding: 24,
                }}
                className="learn-read-scroll ai-daily-article"
              >
                {selected ? (
                  <LearningMarkdown content={mdContent} gfm />
                ) : (
                  <Empty description="从左侧选择一篇文章" />
                )}
              </div>
            </Spin>
          </Card>
        </Col>
      </Row>

      <Drawer
        title="浏览"
        placement="left"
        width={320}
        onClose={() => setBrowseDrawerOpen(false)}
        open={browseDrawerOpen}
      >
        {browseBody}
      </Drawer>
    </div>
  )
}
