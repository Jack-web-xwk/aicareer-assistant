import React from 'react'
import { Card, Tag, Typography, Space, Badge } from 'antd'
import { BookOutlined, ClockCircleOutlined } from '@ant-design/icons'
import type { InterviewQuestion, DifficultyLevel } from '../../types'

const { Text, Paragraph } = Typography

interface QuestionPreviewProps {
  question: InterviewQuestion
  difficulty?: DifficultyLevel
  tags?: string[]
  onSelect?: (question: InterviewQuestion) => void
  showTips?: boolean
  compact?: boolean
}

/**
 * 题目预览卡片组件
 * 用于面试准备页面展示预习题信息
 */
export const QuestionPreview: React.FC<QuestionPreviewProps> = ({
  question,
  difficulty,
  tags,
  onSelect,
  showTips = false,
  compact = false,
}) => {
  // 难度颜色映射
  const getDifficultyColor = (level: DifficultyLevel): string => {
    switch (level) {
      case 'easy':
        return '#52c41a' // green
      case 'medium':
        return '#faad14' // orange
      case 'hard':
        return '#ff4d4f' // red
      default:
        return '#d9d9d9'
    }
  }

  // 维度标签颜色
  const getDimensionColor = (dimension: string): string => {
    const colors: Record<string, string> = {
      technical_skill: 'blue',
      communication: 'purple',
      problem_solving: 'cyan',
      project_experience: 'green',
      cultural_fit: 'orange',
    }
    return colors[dimension] || 'default'
  }

  // 维度中文映射
  const getDimensionLabel = (dimension: string): string => {
    const labels: Record<string, string> = {
      technical_skill: '技术能力',
      communication: '沟通能力',
      problem_solving: '问题解决',
      project_experience: '项目经验',
      cultural_fit: '文化匹配',
    }
    return labels[dimension] || dimension
  }

  const displayTags = tags || question.tags
  const displayDifficulty = difficulty || question.difficulty

  return (
    <Card
      hoverable
      onClick={() => onSelect?.(question)}
      size={compact ? 'small' : 'default'}
      styles={{
        body: { padding: compact ? 12 : 16 },
      }}
      style={{
        marginBottom: 12,
        cursor: 'pointer',
        transition: 'all 0.3s',
        boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
      }}
    >
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {/* 头部：维度和难度 */}
        <Space wrap>
          <Badge
            count={getDimensionLabel(question.dimension)}
            style={{
              backgroundColor: getDimensionColor(question.dimension),
              fontSize: 12,
            }}
          />
          <Tag color={getDifficultyColor(displayDifficulty)}>
            {displayDifficulty === 'easy' && '简单'}
            {displayDifficulty === 'medium' && '中等'}
            {displayDifficulty === 'hard' && '困难'}
          </Tag>
          <Tag icon={<ClockCircleOutlined />} color="gray">
            {question.expected_duration_seconds}s
          </Tag>
        </Space>

        {/* 题目内容 */}
        <Paragraph
          ellipsis={compact ? { rows: 2 } : { rows: 3 }}
          style={{ 
            margin: 0,
            fontSize: compact ? 13 : 14,
            lineHeight: 1.6,
          }}
        >
          <BookOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          {question.content}
        </Paragraph>

        {/* 标签 */}
        {displayTags.length > 0 && (
          <Space wrap size={[4, 4]}>
            {displayTags.slice(0, compact ? 3 : displayTags.length).map((tag) => (
              <Tag key={tag} color="default" style={{ fontSize: 11 }}>
                {tag}
              </Tag>
            ))}
            {displayTags.length > (compact ? 3 : displayTags.length) && (
              <Tag color="default">+{displayTags.length - 3}</Tag>
            )}
          </Space>
        )}

        {/* 提示信息 */}
        {showTips && question.tips && (
          <div
            style={{
              background: '#f6ffed',
              border: '1px solid #b7eb8f',
              borderRadius: 4,
              padding: '8px 12px',
              fontSize: 12,
              color: '#52c41a',
            }}
          >
            <Text strong>💡 提示：</Text>
            <Text>{question.tips}</Text>
          </div>
        )}
      </Space>
    </Card>
  )
}

export default QuestionPreview
