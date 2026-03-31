import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Card,
  List,
  Typography,
  Space,
  Tag,
  Slider,
  Button,
  Empty,
  Spin,
  Tabs,
  Divider,
} from 'antd'
import {
  PlayCircleOutlined,
  HistoryOutlined,
  ThunderboltOutlined,
  LeftOutlined,
} from '@ant-design/icons'
import type {
  ReplaySession,
  FeedbackTimelineItem,
  ComparisonView,
  DimensionType,
} from '../types'
import { replayApi } from '../services/api'
import {
  FeedbackTimeline,
  DimensionScoreCard,
  ReplayComparison,
} from '../components/interview'

const { Text, Title, Paragraph } = Typography

/**
 * 面试回放页面
 * 功能：
 * - 历史面试列表 (按时间排序)
 * - 时间轴 scrubbing (点击跳转对话)
 * - A/B 答案对比播放器
 * - 维度评分详情展示
 * - 使用 Framer Motion 实现平滑转场
 */
const InterviewReplayPage: React.FC = () => {
  // 状态管理
  const [loading, setLoading] = useState(false)
  const [sessions, setSessions] = useState<ReplaySession[]>([])
  const [selectedSession, setSelectedSession] = useState<ReplaySession | null>(null)
  const [activeTab, setActiveTab] = useState('timeline')
  
  // 时间轴相关
  const [currentTimeIndex, setCurrentTimeIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [timelineItems, setTimelineItems] = useState<FeedbackTimelineItem[]>([])
  
  // A/B 对比相关
  const [comparisonData, setComparisonData] = useState<ComparisonView | null>(null)
  const [playingAudio, setPlayingAudio] = useState<'A' | 'B' | null>(null)

  // 加载历史会话
  const loadHistory = async () => {
    setLoading(true)
    try {
      const response = await replayApi.getReplayHistory({ skip: 0, limit: 20 })
      if (response.success && response.data) {
        setSessions(response.data.items)
      }
    } catch (error: unknown) {
      console.error('加载历史失败:', error instanceof Error ? error.message : error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  // 选择会话后初始化时间轴
  useEffect(() => {
    if (!selectedSession) return

    // 构建时间轴数据
    const items: FeedbackTimelineItem[] = []
    
    selectedSession.conversation_history.forEach((msg, index) => {
      // 问题
      if (msg.role === 'assistant') {
        items.push({
          id: `q-${index}`,
          timestamp: msg.timestamp,
          type: 'question',
          content: msg.content,
          dimension: msg.dimension,
          score: msg.score,
        })
      }
      // 回答
      if (msg.role === 'user') {
        items.push({
          id: `a-${index}`,
          timestamp: msg.timestamp,
          type: 'answer',
          content: msg.content,
        })
      }
      // 反馈
      if (msg.feedback) {
        items.push({
          id: `f-${index}`,
          timestamp: msg.timestamp,
          type: 'feedback',
          content: msg.feedback,
          dimension: msg.dimension,
          score: msg.score,
        })
      }
    })

    setTimelineItems(items)
    setCurrentTimeIndex(0)
  }, [selectedSession])

  // 播放控制
  const togglePlay = () => {
    setIsPlaying(!isPlaying)
  }

  // 跳转到指定时间点
  const jumpToTime = (index: number) => {
    setCurrentTimeIndex(index)
    setIsPlaying(false)
  }

  // 处理时间轴项点击
  const handleTimelineSelect = (item: FeedbackTimelineItem) => {
    const index = timelineItems.findIndex((i) => i.id === item.id)
    if (index !== -1) {
      jumpToTime(index)
    }
  }

  // 加载 A/B 对比数据
  const loadComparison = async (messageId: number) => {
    if (!selectedSession) return
    
    try {
      const response = await replayApi.getComparison(selectedSession.session_id, messageId)
      if (response.success && response.data) {
        setComparisonData(response.data)
      }
    } catch (error: unknown) {
      console.error('加载对比数据失败:', error instanceof Error ? error.message : error)
    }
  }

  // 播放音频
  const handlePlayAudio = (answer: 'A' | 'B') => {
    setPlayingAudio(answer === playingAudio ? null : answer)
    // TODO: 实现实际的音频播放逻辑
  }

  // 渲染会话详情
  const renderSessionDetail = () => {
    if (!selectedSession) return null

    return (
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        transition={{ duration: 0.3 }}
      >
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {/* 头部信息 */}
          <Card>
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <Title level={4} style={{ margin: 0 }}>
                  {selectedSession.job_role}
                </Title>
                <Button
                  icon={<LeftOutlined />}
                  onClick={() => setSelectedSession(null)}
                  size="small"
                >
                  返回列表
                </Button>
              </div>
              
              <Space wrap>
                <Tag color="blue">
                  {new Date(selectedSession.started_at).toLocaleString('zh-CN')}
                </Tag>
                <Tag color="green">总分：{selectedSession.total_score}</Tag>
                {selectedSession.tech_stack.map((tech) => (
                  <Tag key={tech} color="default">
                    {tech}
                  </Tag>
                ))}
              </Space>
            </Space>
          </Card>

          {/* 维度评分卡片 */}
          <Card title="维度评分详情">
            <Space direction="horizontal" size="middle" style={{ flexWrap: 'wrap' }}>
              {(Object.keys(selectedSession.dimension_scores) as DimensionType[]).map(
                (dim) => (
                  <div key={dim} style={{ width: 'calc(50% - 8px)', minWidth: 250 }}>
                    <DimensionScoreCard
                      dimension={dim}
                      score={selectedSession.dimension_scores[dim]}
                      feedback={`${dim}维度的详细评价`}
                      trend="stable"
                      compact
                    />
                  </div>
                )
              )}
            </Space>
          </Card>

          {/* 选项卡：时间轴 / A/B 对比 */}
          <Tabs
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key)}
            items={[
              {
                key: 'timeline',
                label: '时间轴回放',
                children: (
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    {/* 播放控制 */}
                    <Card>
                      <Space style={{ width: '100%' }}>
                        <Button
                          type="primary"
                          icon={isPlaying ? <PlayCircleOutlined spin /> : <PlayCircleOutlined />}
                          onClick={togglePlay}
                        >
                          {isPlaying ? '暂停' : '播放'}
                        </Button>
                        <Slider
                          value={currentTimeIndex}
                          max={Math.max(timelineItems.length - 1, 0)}
                          onChange={(value) => jumpToTime(value as number)}
                          style={{ flex: 1 }}
                        />
                        <Text type="secondary">
                          {currentTimeIndex + 1} / {timelineItems.length}
                        </Text>
                      </Space>
                    </Card>

                    {/* 时间轴 */}
                    <FeedbackTimeline
                      feedbackItems={timelineItems}
                      onSelect={handleTimelineSelect}
                      highlightCurrent={timelineItems[currentTimeIndex]?.id}
                    />

                    {/* 当前内容展示 */}
                    {timelineItems[currentTimeIndex] && (
                      <motion.div
                        key={currentTimeIndex}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <Card
                          title={
                            <Tag color={
                              timelineItems[currentTimeIndex].type === 'question' ? 'blue' :
                              timelineItems[currentTimeIndex].type === 'answer' ? 'green' :
                              timelineItems[currentTimeIndex].type === 'feedback' ? 'orange' : 'purple'
                            }>
                              {timelineItems[currentTimeIndex].type}
                            </Tag>
                          }
                        >
                          <Paragraph style={{ fontSize: 15, lineHeight: 1.8 }}>
                            {timelineItems[currentTimeIndex].content}
                          </Paragraph>
                          
                          {timelineItems[currentTimeIndex].score !== undefined && (
                            <Divider />
                          )}
                          
                          {timelineItems[currentTimeIndex].score !== undefined && (
                            <Space>
                              <Text strong>得分：</Text>
                              <Tag color={
                                (timelineItems[currentTimeIndex].score || 0) >= 80
                                  ? 'green'
                                  : 'orange'
                              }>
                                {timelineItems[currentTimeIndex].score}分
                              </Tag>
                            </Space>
                          )}

                          {/* A/B 对比入口 */}
                          {timelineItems[currentTimeIndex].type === 'answer' && (
                            <Button
                              type="dashed"
                              icon={<ThunderboltOutlined />}
                              onClick={() =>
                                loadComparison(currentTimeIndex)
                              }
                              style={{ marginTop: 16 }}
                              block
                            >
                              查看 A/B 答案对比
                            </Button>
                          )}
                        </Card>
                      </motion.div>
                    )}
                  </Space>
                ),
              },
              {
                key: 'comparison',
                label: 'A/B 答案对比',
                children: comparisonData ? (
                  <ReplayComparison
                    answerA={comparisonData.answer_a}
                    answerB={comparisonData.answer_b}
                    comparison_summary={comparisonData.comparison_summary}
                    improvement_suggestions={comparisonData.improvement_suggestions}
                    onPlayAudio={handlePlayAudio}
                    isPlaying={playingAudio !== null}
                  />
                ) : (
                  <Empty description="请在时间轴中选择一条回答查看对比" />
                ),
              },
            ]}
          />
        </Space>
      </motion.div>
    )
  }

  // 渲染会话列表
  const renderSessionList = () => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Card
        title={
          <Space>
            <HistoryOutlined />
            <span>面试历史</span>
          </Space>
        }
      >
        {loading ? (
          <Spin tip="加载中..." />
        ) : sessions.length === 0 ? (
          <Empty description="暂无面试记录" />
        ) : (
          <List
            dataSource={sessions}
            renderItem={(session) => (
              <List.Item
                style={{
                  padding: '16px 0',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f0f0f0',
                }}
                onClick={() => setSelectedSession(session)}
              >
                <motion.div
                  whileHover={{ scale: 1.01 }}
                  style={{ width: '100%' }}
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <Title level={5} style={{ margin: 0 }}>
                        {session.job_role}
                      </Title>
                      <Tag color="green" style={{ fontSize: 12 }}>
                        {session.total_score}分
                      </Tag>
                    </div>
                    <Space wrap size={[4, 4]}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {new Date(session.started_at).toLocaleString('zh-CN')}
                      </Text>
                      {session.tech_stack.slice(0, 5).map((tech) => (
                        <Tag key={tech} color="default" style={{ fontSize: 11 }}>
                          {tech}
                        </Tag>
                      ))}
                    </Space>
                  </Space>
                </motion.div>
              </List.Item>
            )}
          />
        )}
      </Card>
    </motion.div>
  )

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '24px 0' }}>
      <AnimatePresence mode="wait">
        {selectedSession ? (
          <motion.div
            key="detail"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {renderSessionDetail()}
          </motion.div>
        ) : (
          <motion.div key="list">{renderSessionList()}</motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default InterviewReplayPage
