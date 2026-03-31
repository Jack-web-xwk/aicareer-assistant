import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Typography, Space, Statistic, Progress, Spin, Empty, Select, Tag } from 'antd'
import {
  TrophyOutlined,
  FireOutlined,
  CalendarOutlined,
  BookOutlined,
} from '@ant-design/icons'
import type {
  ProgressStats,
  TrendDataPoint,
  HeatmapData,
  DimensionType,
  InterviewHistoryListItem,
} from '../types'
import { progressApi, interviewApi } from '../services/api'
import {
  ProgressRadar,
  TrendChart,
  HeatmapCalendar,
} from '../components/interview'

const { Text, Title } = Typography

/**
 * 进度仪表板页面
 * 功能：
 * - 能力雷达图 (Recharts Radar)
 * - 分数趋势折线图 (Recharts Line)
 * - 练习热力图 (Recharts Calendar)
 * - 最近面试记录卡片
 * - 响应式布局 (768px/1024px 断点)
 */
const ProgressDashboardPage: React.FC = () => {
  // 状态管理
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<ProgressStats | null>(null)
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([])
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null)
  const [recentInterviews, setRecentInterviews] = useState<InterviewHistoryListItem[]>([])
  
  // 时间范围选择
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'quarter' | 'year'>('month')
  const currentMonth = new Date().toISOString().slice(0, 7)

  // 模拟用户 ID（实际应从登录状态获取）
  const userId = 'user_001'

  // 加载数据
  const loadData = async () => {
    setLoading(true)
    try {
      // 并行加载所有数据
      const [statsRes, trendRes, heatmapRes, interviewsRes] = await Promise.all([
        progressApi.getProgressStats({ user_id: userId, timeframe: timeRange }),
        progressApi.getTrendData(userId, timeRange),
        progressApi.getHeatmapData(userId, currentMonth),
        interviewApi.history(0, 5),
      ])

      if (statsRes.success && statsRes.data) {
        setStats(statsRes.data)
      }
      if (trendRes.success && trendRes.data) {
        setTrendData(trendRes.data.data)
      }
      if (heatmapRes.success && heatmapRes.data) {
        setHeatmapData(heatmapRes.data)
      }
      if (interviewsRes.success && interviewsRes.data) {
        setRecentInterviews(interviewsRes.data.items)
      }
    } catch (error: unknown) {
      console.error('加载数据失败:', error instanceof Error ? error.message : error)
    } finally {
      setLoading(false)
    }
  }

  /* eslint-disable react-hooks/exhaustive-deps */
  useEffect(() => {
    loadData()
  }, [timeRange, currentMonth])
  /* eslint-enable react-hooks/exhaustive-deps */

  // 维度中文映射
  const getDimensionLabel = (dim: DimensionType): string => {
    const labels: Record<DimensionType, string> = {
      technical_skill: '技术能力',
      communication: '沟通能力',
      problem_solving: '问题解决',
      project_experience: '项目经验',
      cultural_fit: '文化匹配',
    }
    return labels[dim] || dim
  }

  // 渲染统计卡片
  const renderStatCards = () => {
    if (!stats) return null

    return (
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总面试次数"
              value={stats.total_interviews}
              prefix={<BookOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均分数"
              value={stats.average_score}
              suffix="分"
              precision={1}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="连续练习"
              value={stats.streak_days}
              suffix="天"
              prefix={<FireOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃天数"
              value={stats.activity_days}
              suffix={`/${timeRange === 'week' ? 7 : timeRange === 'month' ? 30 : timeRange === 'quarter' ? 90 : 365}天`}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
    )
  }

  // 渲染维度进度
  const renderDimensionProgress = () => {
    if (!stats) return null

    const dimensions = Object.keys(stats.dimension_averages) as DimensionType[]

    return (
      <Card title="各维度平均分">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {dimensions.map((dim) => {
            const score = stats.dimension_averages[dim]
            const isBest = dim === stats.best_dimension
            const isWeakest = dim === stats.weakest_dimension

            return (
              <div key={dim}>
                <Space style={{ marginBottom: 8 }}>
                  <Text strong>{getDimensionLabel(dim)}</Text>
                  {isBest && <Tag color="gold">🏆 最强</Tag>}
                  {isWeakest && <Tag color="orange">💪 待提升</Tag>}
                </Space>
                <Progress
                  percent={Math.round(score)}
                  strokeColor={
                    isBest ? '#ffd700' : isWeakest ? '#fa8c16' : '#1890ff'
                  }
                  format={() => (
                    <Text strong>{score.toFixed(1)}分</Text>
                  )}
                />
              </div>
            )
          })}
        </Space>
      </Card>
    )
  }

  // 渲染最近面试
  const renderRecentInterviews = () => {
    if (recentInterviews.length === 0) {
      return <Empty description="暂无面试记录" image={Empty.PRESENTED_IMAGE_SIMPLE} />
    }

    return (
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {recentInterviews.map((interview) => (
          <Card
            key={interview.session_id}
            size="small"
            hoverable
            style={{ borderRadius: 6 }}
          >
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <Text strong>{interview.job_role}</Text>
                <Text
                  style={{
                    color:
                      (interview.total_score || 0) >= 80
                        ? '#52c41a'
                        : (interview.total_score || 0) >= 60
                        ? '#faad14'
                        : '#ff4d4f',
                    fontWeight: 'bold',
                  }}
                >
                  {interview.total_score || 0}分
                </Text>
              </div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {new Date(interview.started_at).toLocaleString('zh-CN')}
                {interview.duration_minutes && ` · 时长${interview.duration_minutes}分钟`}
              </Text>
            </Space>
          </Card>
        ))}
      </Space>
    )
  }

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px 0' }}>
      {/* 页面标题 */}
      <Space
        style={{
          marginBottom: 24,
          justifyContent: 'space-between',
          flexWrap: 'wrap',
        }}
      >
        <Title level={3} style={{ margin: 0 }}>
          📊 学习进度仪表板
        </Title>
        <Select
          value={timeRange}
          onChange={(value) => setTimeRange(value)}
          options={[
            { value: 'week', label: '最近一周' },
            { value: 'month', label: '最近一月' },
            { value: 'quarter', label: '最近一季度' },
            { value: 'year', label: '最近一年' },
          ]}
          size="large"
          style={{ minWidth: 150 }}
        />
      </Space>

      {loading ? (
        <Spin tip="加载数据中..." size="large" />
      ) : !stats ? (
        <Empty
          description="暂无进度数据，开始第一次面试吧！"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 统计卡片 */}
          {renderStatCards()}

          {/* 图表区域：响应式布局 */}
          <Row gutter={[16, 16]}>
            {/* 雷达图 */}
            <Col xs={24} lg={12} xl={8}>
              <ProgressRadar
                dimensions={[
                  'technical_skill',
                  'communication',
                  'problem_solving',
                  'project_experience',
                  'cultural_fit',
                ]}
                scores={stats.dimension_averages}
                title="能力雷达图"
                height={250}
                compact
              />
            </Col>

            {/* 维度进度 */}
            <Col xs={24} lg={12} xl={8}>
              {renderDimensionProgress()}
            </Col>

            {/* 最近面试 */}
            <Col xs={24} lg={12} xl={8}>
              <Card title="最近面试" style={{ height: '100%' }}>
                {renderRecentInterviews()}
              </Card>
            </Col>
          </Row>

          {/* 趋势图 */}
          <Row>
            <Col span={24}>
              <TrendChart
                historicalData={trendData}
                metric="score"
                title="分数趋势"
                timeRange={timeRange}
                height={280}
              />
            </Col>
          </Row>

          {/* 热力图 */}
          <Row>
            <Col span={24}>
              <HeatmapCalendar
                activityData={heatmapData!}
                month={currentMonth}
                onDayClick={(date) => console.log('Clicked date:', date)}
              />
            </Col>
          </Row>
        </Space>
      )}
    </div>
  )
}

export default ProgressDashboardPage
