import React from 'react'
import { ResponsiveContainer, Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Tooltip, Legend } from 'recharts'
import { Card, Typography, Space } from 'antd'
import type { DimensionType } from '../../types'

const { Text } = Typography

interface RadarDataPoint {
  dimension: string
  label: string
  score: number
  fullMark: number
}

interface ProgressRadarProps {
  dimensions: DimensionType[]
  scores: Record<DimensionType, number>
  maxScore?: number
  title?: string
  showLegend?: boolean
  showTooltip?: boolean
  height?: number
  compact?: boolean
}

/**
 * 雷达图组件
 * 展示五个能力维度的综合评估
 */
export const ProgressRadar: React.FC<ProgressRadarProps> = ({
  dimensions,
  scores,
  maxScore = 100,
  title,
  showLegend = true,
  showTooltip = true,
  height = 300,
  compact = false,
}) => {
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

  // 准备图表数据
  const chartData: RadarDataPoint[] = dimensions.map((dim) => ({
    dimension: dim,
    label: getDimensionLabel(dim),
    score: scores[dim] || 0,
    fullMark: maxScore,
  }))

  // 自定义 Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as RadarDataPoint
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
          <Space direction="vertical" size={0}>
            <Text strong style={{ fontSize: 13 }}>
              {data.label}
            </Text>
            <Text style={{ fontSize: 12, color: '#666' }}>
              得分：<span style={{ color: getDimensionColor(data.dimension as DimensionType), fontWeight: 'bold' }}>
                {data.score}
              </span> / {data.fullMark}
            </Text>
          </Space>
        </div>
      )
    }
    return null
  }

  return (
    <Card
      size={compact ? 'small' : 'default'}
      title={title}
      styles={{
        body: { padding: compact ? 12 : 16 },
      }}
      style={{ borderRadius: 8 }}
    >
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
            <PolarGrid stroke="#e8e8e8" />
            <PolarAngleAxis
              dataKey="label"
              tick={{ fill: '#666', fontSize: compact ? 11 : 13 }}
              style={{ fontWeight: 500 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, maxScore]}
              tick={{ fill: '#999', fontSize: 10 }}
              tickCount={5}
            />
            <Radar
              name="得分"
              dataKey="score"
              stroke="#1890ff"
              strokeWidth={2}
              fill="#1890ff"
              fillOpacity={0.3}
            />
            {showTooltip && <Tooltip content={<CustomTooltip />} />}
            {showLegend && <Legend />}
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}

export default ProgressRadar
