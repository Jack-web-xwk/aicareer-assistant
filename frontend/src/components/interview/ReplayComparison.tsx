import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, Typography, Space, Tag, Progress, Button, Radio } from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'

const { Text, Paragraph } = Typography

interface ReplayComparisonProps {
  answerA: {
    content: string
    audio_url?: string
    duration_seconds: number
    score: number
    feedback: string
  }
  answerB: {
    content: string
    audio_url?: string
    duration_seconds: number
    score: number
    feedback: string
  }
  comparison_summary: string
  improvement_suggestions: string[]
  onPlayAudio?: (answer: 'A' | 'B') => void
  isPlaying?: boolean
  compact?: boolean
}

/**
 * A/B 答案对比组件
 * 用于面试回放时对比不同版本的答案
 */
export const ReplayComparison: React.FC<ReplayComparisonProps> = ({
  answerA,
  answerB,
  comparison_summary,
  improvement_suggestions,
  onPlayAudio,
  isPlaying = false,
  compact = false,
}) => {
  const [activeAnswer, setActiveAnswer] = useState<'A' | 'B' | null>(null)

  // 格式化时间
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // 获取评分颜色
  const getScoreColor = (score: number): string => {
    if (score >= 85) return '#52c41a'
    if (score >= 70) return '#faad14'
    return '#ff4d4f'
  }

  // 获取评分等级
  const getScoreLevel = (score: number): string => {
    if (score >= 90) return '优秀'
    if (score >= 75) return '良好'
    if (score >= 60) return '中等'
    return '待改进'
  }

  // 处理播放音频
  const handlePlay = (answer: 'A' | 'B', e: React.MouseEvent) => {
    e.stopPropagation()
    onPlayAudio?.(answer)
    setActiveAnswer(answer === activeAnswer ? null : answer)
  }

  return (
    <Card
      size={compact ? 'small' : 'default'}
      styles={{
        body: { padding: compact ? 12 : 16 },
      }}
      style={{ borderRadius: 8 }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* A/B 选择器 */}
        <Radio.Group
          value={activeAnswer || 'A'}
          onChange={(e) => setActiveAnswer(e.target.value)}
          buttonStyle="solid"
          style={{ width: '100%', display: 'flex' }}
        >
          <Radio.Button value="A" style={{ flex: 1, textAlign: 'center' }}>
            <Space>
              <ThunderboltOutlined />
              答案 A（原始）
            </Space>
          </Radio.Button>
          <Radio.Button value="B" style={{ flex: 1, textAlign: 'center' }}>
            <Space>
              <CheckCircleOutlined />
              答案 B（优化）
            </Space>
          </Radio.Button>
        </Radio.Group>

        {/* 答案对比展示 */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeAnswer}
            initial={{ opacity: 0, x: activeAnswer === 'A' ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: activeAnswer === 'A' ? 20 : -20 }}
            transition={{ duration: 0.3 }}
          >
            {activeAnswer === 'A' && (
              <div
                style={{
                  padding: 16,
                  background: '#f6ffed',
                  border: '1px solid #b7eb8f',
                  borderRadius: 8,
                }}
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  {/* 头部：分数和时长 */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Space>
                      <Tag color="blue">答案 A</Tag>
                      <Text strong style={{ fontSize: 16, color: getScoreColor(answerA.score) }}>
                        {answerA.score}分
                      </Text>
                      <Text type="secondary">{getScoreLevel(answerA.score)}</Text>
                    </Space>
                    <Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatTime(answerA.duration_seconds)}
                      </Text>
                      {onPlayAudio && (
                        <Button
                          type="text"
                          icon={isPlaying && activeAnswer === 'A' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                          onClick={(e) => handlePlay('A', e)}
                          size="small"
                        />
                      )}
                    </Space>
                  </div>

                  {/* 进度条 */}
                  <Progress
                    percent={answerA.score}
                    strokeColor={getScoreColor(answerA.score)}
                    trailColor="#f0f0f0"
                    showInfo={false}
                    size="small"
                  />

                  {/* 答案内容 */}
                  <Paragraph
                    ellipsis={{ rows: 4 }}
                    style={{
                      margin: 0,
                      fontSize: 14,
                      lineHeight: 1.8,
                      color: '#333',
                    }}
                  >
                    {answerA.content}
                  </Paragraph>

                  {/* 反馈 */}
                  <div
                    style={{
                      background: 'rgba(255,255,255,0.5)',
                      padding: '8px 12px',
                      borderRadius: 4,
                      marginTop: 8,
                    }}
                  >
                    <Text strong style={{ fontSize: 12, color: '#52c41a' }}>
                      💡 反馈：
                    </Text>
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{
                        margin: '4px 0 0 0',
                        fontSize: 12,
                        color: '#666',
                      }}
                    >
                      {answerA.feedback}
                    </Paragraph>
                  </div>
                </Space>
              </div>
            )}

            {activeAnswer === 'B' && (
              <div
                style={{
                  padding: 16,
                  background: '#e6f7ff',
                  border: '1px solid #91d5ff',
                  borderRadius: 8,
                }}
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  {/* 头部：分数和时长 */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <Space>
                      <Tag color="purple">答案 B</Tag>
                      <Text strong style={{ fontSize: 16, color: getScoreColor(answerB.score) }}>
                        {answerB.score}分
                      </Text>
                      <Text type="secondary">{getScoreLevel(answerB.score)}</Text>
                    </Space>
                    <Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {formatTime(answerB.duration_seconds)}
                      </Text>
                      {onPlayAudio && (
                        <Button
                          type="text"
                          icon={isPlaying && activeAnswer === 'B' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                          onClick={(e) => handlePlay('B', e)}
                          size="small"
                        />
                      )}
                    </Space>
                  </div>

                  {/* 进度条 */}
                  <Progress
                    percent={answerB.score}
                    strokeColor={getScoreColor(answerB.score)}
                    trailColor="#f0f0f0"
                    showInfo={false}
                    size="small"
                  />

                  {/* 答案内容 */}
                  <Paragraph
                    ellipsis={{ rows: 4 }}
                    style={{
                      margin: 0,
                      fontSize: 14,
                      lineHeight: 1.8,
                      color: '#333',
                    }}
                  >
                    {answerB.content}
                  </Paragraph>

                  {/* 反馈 */}
                  <div
                    style={{
                      background: 'rgba(255,255,255,0.5)',
                      padding: '8px 12px',
                      borderRadius: 4,
                      marginTop: 8,
                    }}
                  >
                    <Text strong style={{ fontSize: 12, color: '#1890ff' }}>
                      💡 反馈：
                    </Text>
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{
                        margin: '4px 0 0 0',
                        fontSize: 12,
                        color: '#666',
                      }}
                    >
                      {answerB.feedback}
                    </Paragraph>
                  </div>
                </Space>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* 对比总结 */}
        <div
          style={{
            padding: '12px 16px',
            background: '#fff7e6',
            border: '1px solid #ffd591',
            borderRadius: 8,
          }}
        >
          <Text strong style={{ color: '#fa8c16', display: 'block', marginBottom: 8 }}>
            📊 对比分析：
          </Text>
          <Paragraph
            ellipsis={{ rows: 3 }}
            style={{ margin: 0, fontSize: 13, color: '#666', lineHeight: 1.6 }}
          >
            {comparison_summary}
          </Paragraph>
        </div>

        {/* 改进建议 */}
        {improvement_suggestions.length > 0 && (
          <div
            style={{
              padding: '12px 16px',
              background: '#f9f0ff',
              border: '1px solid #d3adf7',
              borderRadius: 8,
            }}
          >
            <Text strong style={{ color: '#722ed1', display: 'block', marginBottom: 8 }}>
              🎯 改进建议：
            </Text>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              {improvement_suggestions.slice(0, 3).map((suggestion, index) => (
                <div key={index} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                  <div
                    style={{
                      minWidth: 16,
                      height: 16,
                      borderRadius: '50%',
                      background: '#722ed1',
                      color: 'white',
                      fontSize: 10,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                    }}
                  >
                    {index + 1}
                  </div>
                  <Text style={{ fontSize: 13, color: '#666', flex: 1 }}>
                    {suggestion}
                  </Text>
                </div>
              ))}
              {improvement_suggestions.length > 3 && (
                <Text type="secondary" style={{ fontSize: 12, marginLeft: 24 }}>
                  还有 {improvement_suggestions.length - 3} 条建议...
                </Text>
              )}
            </Space>
          </div>
        )}
      </Space>
    </Card>
  )
}

export default ReplayComparison
