import { useMemo, useRef } from 'react'
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Collapse,
  Empty,
  Input,
  Pagination,
  Radio,
  Row,
  Col,
  Select,
  Space,
  Spin,
  Switch,
  Tag,
  Typography,
  InputNumber,
} from 'antd'
import {
  BankOutlined,
  EnvironmentOutlined,
  FieldTimeOutlined,
  LinkOutlined,
} from '@ant-design/icons'

import { useJobSearchStore } from '../stores/jobSearchStore'
import type { JobSource } from '../types'

const { Title, Text, Paragraph } = Typography

const SOURCE_LABEL: Record<JobSource, string> = {
  boss: 'Boss直聘',
  zhaopin: '智联招聘',
  yupao: '鱼泡',
  link: '链接',
}

const SOURCE_COLOR: Record<JobSource, string> = {
  boss: 'blue',
  zhaopin: 'green',
  yupao: 'orange',
  link: 'purple',
}

const SUGGEST_KEYWORDS = ['Java', 'Python', '前端开发', '产品经理', '数据分析师']

const CITY_OPTIONS = [
  { label: '全国', value: '' },
  { label: '北京', value: '北京' },
  { label: '上海', value: '上海' },
  { label: '广州', value: '广州' },
  { label: '深圳', value: '深圳' },
  { label: '杭州', value: '杭州' },
  { label: '成都', value: '成都' },
]

export default function JobsPage() {
  const keyword = useJobSearchStore((s) => s.keyword)
  const company_keyword = useJobSearchStore((s) => s.company_keyword)
  const match_mode = useJobSearchStore((s) => s.match_mode)
  const city = useJobSearchStore((s) => s.city)
  const salary_min = useJobSearchStore((s) => s.salary_min)
  const salary_max = useJobSearchStore((s) => s.salary_max)
  const experience = useJobSearchStore((s) => s.experience)
  const sources = useJobSearchStore((s) => s.sources)
  const sort_by = useJobSearchStore((s) => s.sort_by)
  const sort_order = useJobSearchStore((s) => s.sort_order)
  const page = useJobSearchStore((s) => s.page)
  const page_size = useJobSearchStore((s) => s.page_size)
  const items = useJobSearchStore((s) => s.items)
  const total = useJobSearchStore((s) => s.total)
  const sources_used = useJobSearchStore((s) => s.sources_used)
  const cached = useJobSearchStore((s) => s.cached)
  const warning = useJobSearchStore((s) => s.warning)
  const loading = useJobSearchStore((s) => s.loading)
  const lastError = useJobSearchStore((s) => s.lastError)
  const liveSearch = useJobSearchStore((s) => s.liveSearch)
  const history = useJobSearchStore((s) => s.history)

  const setKeyword = useJobSearchStore((s) => s.setKeyword)
  const setCompanyKeyword = useJobSearchStore((s) => s.setCompanyKeyword)
  const setMatchMode = useJobSearchStore((s) => s.setMatchMode)
  const setCity = useJobSearchStore((s) => s.setCity)
  const setSalaryMin = useJobSearchStore((s) => s.setSalaryMin)
  const setSalaryMax = useJobSearchStore((s) => s.setSalaryMax)
  const setExperience = useJobSearchStore((s) => s.setExperience)
  const setSources = useJobSearchStore((s) => s.setSources)
  const setSortBy = useJobSearchStore((s) => s.setSortBy)
  const setSortOrder = useJobSearchStore((s) => s.setSortOrder)
  const setPage = useJobSearchStore((s) => s.setPage)
  const setPageSize = useJobSearchStore((s) => s.setPageSize)
  const setLiveSearch = useJobSearchStore((s) => s.setLiveSearch)
  const runSearch = useJobSearchStore((s) => s.runSearch)
  const applyHistoryEntry = useJobSearchStore((s) => s.applyHistoryEntry)
  const resetFilters = useJobSearchStore((s) => s.resetFilters)

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const onKeywordChange = (value: string) => {
    setKeyword(value)
    if (!liveSearch) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setPage(1)
      void runSearch({ saveHistory: true })
    }, 300)
  }

  const allSourceOptions = useMemo(
    () =>
      (['boss', 'zhaopin', 'yupao'] as JobSource[]).map((v) => ({
        label: SOURCE_LABEL[v],
        value: v,
      })),
    []
  )

  const onSearchClick = () => {
    setPage(1)
    void runSearch({ saveHistory: true })
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={3} style={{ marginBottom: 8 }}>
            职位搜索
          </Title>
          <Text type="secondary">
            聚合多平台列表（MVP 爬虫）；结果仅供学习参考，请遵守各站服务条款与限流策略。
            若需按<strong>单个链接</strong>爬取并入库，请使用菜单「目标岗位」。
          </Text>
        </div>

        <Card>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Row gutter={[16, 16]}>
              <Col xs={24} md={12}>
                <Text strong>关键词</Text>
                <Input.Search
                  placeholder="职位关键词，如 前端、Java"
                  value={keyword}
                  onChange={(e) => onKeywordChange(e.target.value)}
                  onSearch={() => onSearchClick()}
                  enterButton="搜索"
                  loading={loading}
                  allowClear
                />
              </Col>
              <Col xs={24} md={12}>
                <Text strong>公司名称</Text>
                <Input
                  placeholder="可选：过滤公司名"
                  value={company_keyword}
                  onChange={(e) => setCompanyKeyword(e.target.value)}
                  onPressEnter={() => onSearchClick()}
                  allowClear
                />
              </Col>
            </Row>

            <Space wrap>
              <Text>实时搜索（防抖 300ms）</Text>
              <Switch checked={liveSearch} onChange={setLiveSearch} />
              <Button onClick={() => resetFilters()}>重置条件</Button>
            </Space>

            <Collapse
              items={[
                {
                  key: 'adv',
                  label: '高级筛选',
                  children: (
                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                      <div>
                        <Text strong>匹配模式</Text>
                        <Radio.Group
                          value={match_mode}
                          onChange={(e) => setMatchMode(e.target.value)}
                          style={{ marginLeft: 12 }}
                        >
                          <Radio.Button value="fuzzy">模糊</Radio.Button>
                          <Radio.Button value="exact">精确（公司名）</Radio.Button>
                        </Radio.Group>
                      </div>
                      <Row gutter={[16, 16]}>
                        <Col xs={24} sm={12} md={8}>
                          <Text strong>城市</Text>
                          <Select
                            style={{ width: '100%', marginTop: 8 }}
                            options={CITY_OPTIONS}
                            value={city || ''}
                            onChange={(v) => setCity(v)}
                            placeholder="选择城市"
                          />
                        </Col>
                        <Col xs={24} sm={12} md={8}>
                          <Text strong>薪资下限（元/月，可选）</Text>
                          <InputNumber
                            style={{ width: '100%', marginTop: 8 }}
                            min={0}
                            placeholder="如 15000"
                            value={salary_min}
                            onChange={(v) => setSalaryMin(v ?? undefined)}
                          />
                        </Col>
                        <Col xs={24} sm={12} md={8}>
                          <Text strong>薪资上限（元/月，可选）</Text>
                          <InputNumber
                            style={{ width: '100%', marginTop: 8 }}
                            min={0}
                            placeholder="如 30000"
                            value={salary_max}
                            onChange={(v) => setSalaryMax(v ?? undefined)}
                          />
                        </Col>
                      </Row>
                      <div>
                        <Text strong>经验关键词（可选）</Text>
                        <Input
                          style={{ marginTop: 8, maxWidth: 400 }}
                          placeholder="如 3-5年、应届"
                          value={experience}
                          onChange={(e) => setExperience(e.target.value)}
                        />
                      </div>
                      <div>
                        <Text strong>数据源</Text>
                        <div style={{ marginTop: 8 }}>
                          <Checkbox.Group
                            options={allSourceOptions}
                            value={sources}
                            onChange={(v) => setSources(v as JobSource[])}
                          />
                        </div>
                      </div>
                    </Space>
                  ),
                },
              ]}
            />

            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} sm={12} md={8}>
                <Text strong>排序</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  value={`${sort_by}:${sort_order}`}
                  onChange={(v) => {
                    const [sb, so] = v.split(':') as [typeof sort_by, typeof sort_order]
                    setSortBy(sb)
                    setSortOrder(so)
                    void runSearch()
                  }}
                  options={[
                    { label: '发布时间 · 新→旧', value: 'published_at:desc' },
                    { label: '发布时间 · 旧→新', value: 'published_at:asc' },
                    { label: '薪资文本 · 高→低', value: 'salary:desc' },
                    { label: '薪资文本 · 低→高', value: 'salary:asc' },
                  ]}
                />
              </Col>
              <Col xs={24} sm={12} md={8}>
                <Text strong>每页条数</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  value={page_size}
                  onChange={(v) => {
                    setPageSize(v)
                    setPage(1)
                    void runSearch()
                  }}
                  options={[
                    { label: '10', value: 10 },
                    { label: '15', value: 15 },
                    { label: '30', value: 30 },
                  ]}
                />
              </Col>
            </Row>
          </Space>
        </Card>

        {lastError ? (
          <Alert type="error" message={lastError} showIcon closable />
        ) : null}
        {warning ? (
          <Alert type="warning" message={warning} showIcon />
        ) : null}

        <Card>
          <Space style={{ marginBottom: 16 }} wrap>
            <Text>
              共 <Text strong>{total}</Text> 条
            </Text>
            {sources_used.length ? (
              <Text type="secondary">
                数据源：{sources_used.join('、')}
              </Text>
            ) : null}
            {cached ? <Tag color="cyan">来自缓存</Tag> : null}
          </Space>

          <Spin spinning={loading}>
            {items.length === 0 && !loading ? (
              <Empty
                description="暂无职位，试试换个关键词或数据源"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Paragraph type="secondary">推荐关键词：</Paragraph>
                <Space wrap>
                  {SUGGEST_KEYWORDS.map((k) => (
                    <Button
                      key={k}
                      size="small"
                      onClick={() => {
                        setKeyword(k)
                        setPage(1)
                        void runSearch({ saveHistory: true })
                      }}
                    >
                      {k}
                    </Button>
                  ))}
                </Space>
              </Empty>
            ) : (
              <Row gutter={[16, 16]}>
                {items.map((job) => (
                  <Col xs={24} md={12} key={job.detail_url}>
                    <Card
                      size="small"
                      title={
                        <a
                          href={job.detail_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {job.title} <LinkOutlined />
                        </a>
                      }
                      extra={
                        <Tag color={SOURCE_COLOR[job.source]}>{SOURCE_LABEL[job.source]}</Tag>
                      }
                    >
                      <Space direction="vertical" size={4} style={{ width: '100%' }}>
                        <Text>
                          <BankOutlined /> {job.company_name || '—'}
                        </Text>
                        <Text type="secondary">
                          <EnvironmentOutlined /> {job.location || '—'} · {job.salary_text || '薪资面议'}
                        </Text>
                        <Text type="secondary">
                          <FieldTimeOutlined />{' '}
                          {job.published_at ? String(job.published_at) : '—'} ·{' '}
                          {job.experience_text || '经验不限'} · {job.education_text || '学历不限'}
                        </Text>
                      </Space>
                    </Card>
                  </Col>
                ))}
              </Row>
            )}
          </Spin>

          {total > 0 ? (
            <div style={{ marginTop: 24, textAlign: 'right' }}>
              <Pagination
                current={page}
                pageSize={page_size}
                total={total}
                showSizeChanger={false}
                onChange={(p) => {
                  setPage(p)
                  void runSearch()
                }}
              />
            </div>
          ) : null}
        </Card>

        {history.length > 0 ? (
          <Card title="搜索历史（本地）" size="small">
            <Space wrap>
              {history.map((h, i) => (
                <Button key={`${h.savedAt}-${i}`} size="small" onClick={() => applyHistoryEntry(h)}>
                  {h.label}
                </Button>
              ))}
            </Space>
          </Card>
        ) : null}
      </Space>
    </div>
  )
}
