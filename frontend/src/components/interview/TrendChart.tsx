import React from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
  AreaChart,
} from 'recharts'
import { Card, Typography, Space, Select } from 'antd'
import type { TrendDataPoint, DimensionType } from '../../types'

const { Text } = Typography

interface TrendChartProps {
  historicalData: TrendDataPoint[]
  metric?: 'score' | 'count' | 'dimension'
  dimensions?: DimensionType[]
  title?: string
  showArea?: boolean
  showGrid?: boolean
  height?: number
  compact?: boolean
  timeRange?: 'week' | 'month' | 'quarter' | 'year'
  onTimeRangeChange?: (range: 'week' | 'month' | 'quarter' | 'year') => void
}

/**
 * 趋势图组件
 * 展示分数或数量的时间趋势
 */
export const TrendChart: React.FC<TrendChartProps> = ({
  historicalData,
  metric = 'score',
  dimensions,
  title,
  showArea = false,
  showGrid = true,
  height = 300,
  compact = false,
  timeRange,
  onTimeRangeChange,
}) => {
  // 维度颜色映射
  const getDimensionColor = (dim: DimensionType): string => {
    const colors: Record<DimensionType, string> = {
      technical_skill: '#1890ff',
      communication: '#722ed1',
      problem_solving: '#13c2c2',
      project_experience: '#52c41a',
      cultural_fit: '#fa8c16',
    }
    return colors[dim] || '#d9d9d9'
  }

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

  // 格式化日期显示
  const formatDate = (date: string): string => {
    const d = new Date(date)
    if (timeRange === 'week') {
      return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
    }
    if (timeRange === 'month') {
      return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
    }
    if (timeRange === 'quarter') {
      return d.toLocaleDateString('zh-CN', { month: 'numeric' })
    }
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'numeric' })
  }

  // 自定义 Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #d9d9d9',
            borderRadius: 4,
            padding: '8px 12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          }}
        >
          <Space direction="vertical" size={4}>
            <Text strong style={{ fontSize: 13 }}>
              {label}
            </Text>
            {payload.map((p: any, index: number) => (
              <div key={index} style={{ fontSize: 12 }}>
                <span style={{ color: p.color, marginRight: 4 }}>●</span>
                <span style={{ color: '#333' }}>
                  {p.name}: <strong>{p.value}</strong>
                  {metric === 'score' && ' 分'}
                  {metric === 'count' && ' 次'}
                </span>
              </div>
            ))}
          </Space>
        </div>
      )
    }
    return null
  }

  // 时间范围选项
  const timeRangeOptions = [
    { value: 'week', label: '最近一周' },
    { value: 'month', label: '最近一月' },
    { value: 'quarter', label: '最近一季度' },
    { value: 'year', label: '最近一年' },
  ]

  // 渲染图表
  const renderChart = () => {
    const ChartComponent = showArea ? AreaChart : LineChart

    return (
      <ResponsiveContainer width="100%" height="100%">
        <ChartComponent data={historicalData}>
          {showGrid && (
            <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
          )}
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fill: '#666', fontSize: compact ? 10 : 12 }}
            axisLine={{ stroke: '#d9d9d9' }}
          />
          <YAxis
            tick={{ fill: '#666', fontSize: compact ? 10 : 12 }}
            axisLine={{ stroke: '#d9d9d9' }}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* 总分趋势线 */}
          {(metric === 'score' || metric === 'count') && (
            <>
              {showArea ? (
                <Area
                  type="monotone"
                  dataKey={metric === 'score' ? 'score' : 'interview_count'}
                  name={metric === 'score' ? '平均分数' : '面试次数'}
                  stroke="#1890ff"
                  fill="#1890ff"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              ) : (
                <Line
                  type="monotone"
                  dataKey={metric === 'score' ? 'score' : 'interview_count'}
                  name={metric === 'score' ? '平均分数' : '面试次数'}
                  stroke="#1890ff"
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#1890ff' }}
                  activeDot={{ r: 6 }}
                />
              )}
            </>
          )}

          {/* 各维度趋势线 */}
          {metric === 'dimension' &&
            dimensions?.map((dim) => (
              <Line
                key={dim}
                type="monotone"
                dataKey={(data: TrendDataPoint) =>
                  data.dimension_scores?.[dim] || 0
                }
                name={getDimensionLabel(dim)}
                stroke={getDimensionColor(dim)}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
              />
            ))}
        </ChartComponent>
      </ResponsiveContainer>
    )
  }

  return (
    <Card
      size={compact ? 'small' : 'default'}
      title={
        <Space>
          <span>{title || '趋势分析'}</span>
          {onTimeRangeChange && (
            <Select
              value={timeRange || 'month'}
              options={timeRangeOptions}
              onChange={onTimeRangeChange}
              size="small"
              style={{ marginLeft: 'auto' }}
            />
          )}
        </Space>
      }
      styles={{
        body: { padding: compact ? 12 : 16 },
      }}
      style={{ borderRadius: 8 }}
    >
      <div style={{ width: '100%', height }}>{renderChart()}</div>
    </Card>
  )
}

export default TrendChart
