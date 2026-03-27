import React from 'react'
import { Timeline, Typography, Space, Tag, Card } from 'antd'
import {
  QuestionCircleOutlined,
  CheckCircleOutlined,
  StarOutlined,
  ClockCircleOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import type { FeedbackTimelineItem, DimensionType } from '../../types'

const { Text, Paragraph } = Typography

interface FeedbackTimelineProps {
  feedbackItems: FeedbackTimelineItem[]
  onSelect?: (item: FeedbackTimelineItem) => void
  showTime?: boolean
  compact?: boolean
  highlightCurrent?: string // 当前高亮的 item id
}

/**
 * 时间轴反馈组件
 * 以时间轴形式展示面试过程中的问题和反馈
 */
export const FeedbackTimeline: React.FC<FeedbackTimelineProps> = ({
  feedbackItems,
  onSelect,
  showTime = true,
  compact = false,
  highlightCurrent,
}) => {
  // 维度颜色映射
  const getDimensionColor = (dimension?: DimensionType): string => {
    if (!dimension) return 'default'
    const colors: Record<DimensionType, string> = {
      technical_skill: 'blue',
      communication: 'purple',
      problem_solving: 'cyan',
      project_experience: 'green',
      cultural_fit: 'orange',
    }
    return colors[dimension] || 'default'
  }

  // 维度中文映射
  const getDimensionLabel = (dimension?: DimensionType): string => {
    if (!dimension) return ''
    const labels: Record<DimensionType, string> = {
      technical_skill: '技术能力',
      communication: '沟通能力',
      problem_solving: '问题解决',
      project_experience: '项目经验',
      cultural_fit: '文化匹配',
    }
    return labels[dimension] || dimension
  }

  // 获取图标
  const getIcon = (type: FeedbackTimelineItem['type'], item: FeedbackTimelineItem) => {
    if (item.icon) {
      return <span style={{ fontSize: 16 }}>{item.icon}</span>
    }
    switch (type) {
      case 'question':
        return <QuestionCircleOutlined style={{ color: '#1890ff' }} />
      case 'answer':
        return <MessageOutlined style={{ color: '#52c41a' }} />
      case 'feedback':
        return <CheckCircleOutlined style={{ color: '#faad14' }} />
      case 'milestone':
        return <StarOutlined style={{ color: '#722ed1' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  // 格式化时间
  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  // 处理点击
  const handleItemClick = (item: FeedbackTimelineItem) => {
    onSelect?.(item)
  }

  return (
    <Card
      size={compact ? 'small' : 'default'}
      styles={{
        body: { padding: compact ? 12 : 16 },
      }}
      style={{ borderRadius: 8 }}
    >
      <Timeline
        items={feedbackItems.map((item) => ({
          key: item.id,
          color: getDimensionColor(item.dimension),
          dot: getIcon(item.type, item),
          children: (
            <div
              onClick={() => handleItemClick(item)}
              style={{
                padding: '10px 12px',
                borderRadius: 6,
                background:
                  highlightCurrent === item.id ? '#e6f7ff' : 'transparent',
                border:
                  highlightCurrent === item.id
                    ? '1px solid #1890ff'
                    : '1px solid transparent',
                cursor: onSelect ? 'pointer' : 'default',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                if (onSelect && highlightCurrent !== item.id) {
                  e.currentTarget.style.background = '#f5f5f5'
                }
              }}
              onMouseLeave={(e) => {
                if (onSelect && highlightCurrent !== item.id) {
                  e.currentTarget.style.background = 'transparent'
                }
              }}
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                {/* 头部：类型和时间 */}
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Space wrap size={[4, 4]}>
                    <Tag color={getDimensionColor(item.dimension)}>
                      {item.type === 'question' && '问题'}
                      {item.type === 'answer' && '回答'}
                      {item.type === 'feedback' && '反馈'}
                      {item.type === 'milestone' && '里程碑'}
                    </Tag>
                    {item.dimension && (
                      <Tag color={getDimensionColor(item.dimension)}>
                        {getDimensionLabel(item.dimension)}
                      </Tag>
                    )}
                    {item.score !== undefined && (
                      <Tag color={item.score >= 80 ? 'green' : item.score >= 60 ? 'orange' : 'red'}>
                        得分：{item.score}
                      </Tag>
                    )}
                  </Space>
                  {showTime && (
                    <Text
                      type="secondary"
                      style={{ fontSize: 11 }}
                    >
                      {formatTime(item.timestamp)}
                    </Text>
                  )}
                </div>

                {/* 内容 */}
                <Paragraph
                  ellipsis={compact ? { rows: 2 } : undefined}
                  style={{
                    margin: 0,
                    fontSize: compact ? 13 : 14,
                    lineHeight: 1.6,
                    color: '#333',
                  }}
                >
                  {item.content}
                </Paragraph>
              </Space>
            </div>
          ),
        }))}
      />
    </Card>
  )
}

export default FeedbackTimeline
