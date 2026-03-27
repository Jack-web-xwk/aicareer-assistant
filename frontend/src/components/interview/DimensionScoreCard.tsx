import React from 'react'
import { Card, Progress, Typography, Space, Tag, Tooltip } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  TrophyOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import type { DimensionType } from '../../types'

const { Text, Paragraph } = Typography

interface DimensionScoreCardProps {
  dimension: DimensionType
  score: number
  max_score?: number
  feedback: string
  trend?: 'up' | 'down' | 'stable'
  previous_score?: number
  strengths?: string[]
  areas_to_improve?: string[]
  onClick?: () => void
  showDetails?: boolean
  compact?: boolean
}

/**
 * 维度评分卡组件
 * 展示单个能力维度的评分、趋势和反馈信息
 */
export const DimensionScoreCard: React.FC<DimensionScoreCardProps> = ({
  dimension,
  score,
  max_score = 100,
  feedback,
  trend = 'stable',
  previous_score,
  strengths = [],
  areas_to_improve = [],
  onClick,
  showDetails = true,
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

  // 维度图标颜色
  const getDimensionColor = (dim: DimensionType): string => {
    const colors: Record<DimensionType, string> = {
      technical_skill: '#1890ff', // blue
      communication: '#722ed1', // purple
      problem_solving: '#13c2c2', // cyan
      project_experience: '#52c41a', // green
      cultural_fit: '#fa8c16', // orange
    }
    return colors[dim] || '#d9d9d9'
  }

  // 计算百分比
  const percentage = Math.round((score / max_score) * 100)

  // 获取评分等级
  const getScoreLevel = (percent: number): string => {
    if (percent >= 90) return '优秀'
    if (percent >= 75) return '良好'
    if (percent >= 60) return '中等'
    if (percent >= 40) return '待改进'
    return '需加强'
  }

  // 趋势图标
  const TrendIcon = () => {
    if (trend === 'up') {
      return (
        <ArrowUpOutlined
          style={{ color: '#52c41a', fontSize: 16 }}
        />
      )
    }
    if (trend === 'down') {
      return (
        <ArrowDownOutlined
          style={{ color: '#ff4d4f', fontSize: 16 }}
        />
      )
    }
    return <MinusOutlined style={{ color: '#d9d9d9', fontSize: 16 }} />
  }

  // 趋势文字
  const getTrendText = () => {
    if (!previous_score) return ''
    const diff = score - previous_score
    if (diff > 0) return `+${diff}`
    if (diff < 0) return `${diff}`
    return '0'
  }

  return (
    <Card
      hoverable={!!onClick}
      onClick={onClick}
      size={compact ? 'small' : 'default'}
      style={{
        borderRadius: 8,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        cursor: onClick ? 'pointer' : 'default',
      }}
      styles={{
        body: { padding: compact ? 12 : 16 },
      }}
    >
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {/* 头部：维度名称和分数 */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Space>
            <div
              style={{
                width: 4,
                height: 16,
                background: getDimensionColor(dimension),
                borderRadius: 2,
              }}
            />
            <Text strong style={{ fontSize: compact ? 14 : 15 }}>
              {getDimensionLabel(dimension)}
            </Text>
          </Space>
          <Space>
            {trend && (
              <Tooltip
                title={
                  previous_score
                    ? `上次得分：${previous_score}`
                    : '暂无对比数据'
                }
              >
                <Tag color={trend === 'up' ? 'green' : trend === 'down' ? 'red' : 'gray'}>
                  <Space size={4}>
                    <TrendIcon />
                    {getTrendText()}
                  </Space>
                </Tag>
              </Tooltip>
            )}
            <Text
              strong
              style={{
                fontSize: compact ? 18 : 20,
                color: getDimensionColor(dimension),
              }}
            >
              {score}
            </Text>
          </Space>
        </div>

        {/* 进度条 */}
        <Progress
          percent={percentage}
          strokeColor={getDimensionColor(dimension)}
          trailColor="#f0f0f0"
          format={() => (
            <Text
              style={{ fontSize: 12, color: '#666' }}
            >
              {getScoreLevel(percentage)}
            </Text>
          )}
          size={compact ? 'small' : 'default'}
        />

        {/* 反馈文案 */}
        {feedback && (
          <Paragraph
            ellipsis={compact ? { rows: 2 } : undefined}
            style={{
              margin: 0,
              fontSize: compact ? 12 : 13,
              color: '#666',
              lineHeight: 1.6,
            }}
          >
            {feedback}
          </Paragraph>
        )}

        {/* 详细信息 */}
        {showDetails && (strengths.length > 0 || areas_to_improve.length > 0) && (
          <Space direction="vertical" size="small" style={{ width: '100%', marginTop: 8 }}>
            {/* 优势 */}
            {strengths.length > 0 && (
              <div
                style={{
                  background: '#f6ffed',
                  border: '1px solid #b7eb8f',
                  borderRadius: 4,
                  padding: '8px 12px',
                }}
              >
                <Space size={4} style={{ display: 'flex', flexWrap: 'wrap' }}>
                  <TrophyOutlined style={{ color: '#52c41a' }} />
                  <Text strong style={{ fontSize: 12, color: '#52c41a' }}>
                    优势：
                  </Text>
                  {strengths.slice(0, 2).map((item, idx) => (
                    <Tag key={idx} color="green" style={{ fontSize: 11, margin: 0 }}>
                      {item}
                    </Tag>
                  ))}
                  {strengths.length > 2 && (
                    <Tag color="green" style={{ fontSize: 11, margin: 0 }}>
                      +{strengths.length - 2}
                    </Tag>
                  )}
                </Space>
              </div>
            )}

            {/* 待改进 */}
            {areas_to_improve.length > 0 && (
              <div
                style={{
                  background: '#fff7e6',
                  border: '1px solid #ffd591',
                  borderRadius: 4,
                  padding: '8px 12px',
                }}
              >
                <Space size={4} style={{ display: 'flex', flexWrap: 'wrap' }}>
                  <BulbOutlined style={{ color: '#fa8c16' }} />
                  <Text strong style={{ fontSize: 12, color: '#fa8c16' }}>
                    建议：
                  </Text>
                  {areas_to_improve.slice(0, 2).map((item, idx) => (
                    <Tag key={idx} color="orange" style={{ fontSize: 11, margin: 0 }}>
                      {item}
                    </Tag>
                  ))}
                  {areas_to_improve.length > 2 && (
                    <Tag color="orange" style={{ fontSize: 11, margin: 0 }}>
                      +{areas_to_improve.length - 2}
                    </Tag>
                  )}
                </Space>
              </div>
            )}
          </Space>
        )}
      </Space>
    </Card>
  )
}

export default DimensionScoreCard
