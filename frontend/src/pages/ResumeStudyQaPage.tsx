import { useCallback, useEffect, useState } from 'react'
import {
  Card,
  Typography,
  Select,
  Button,
  Space,
  message,
  Collapse,
  Tag,
  Alert,
} from 'antd'
import { QuestionCircleOutlined, HistoryOutlined, RocketOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { resumeApi } from '../services/api'
import type { ResumeUploadListItem, StudyQaItem } from '../types'
import type { CSSProperties } from 'react'

const { Title, Paragraph, Text } = Typography

const cardStyle: CSSProperties = {
  background: 'var(--color-bg-primary)',
  border: '1px solid var(--color-border)',
  boxShadow: 'var(--shadow-sm)',
}

function ResumeStudyQaPage() {
  const [listLoading, setListLoading] = useState(true)
  const [optimizedList, setOptimizedList] = useState<ResumeUploadListItem[]>([])
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [generating, setGenerating] = useState(false)
  const [items, setItems] = useState<StudyQaItem[]>([])
  const [lastSessionId, setLastSessionId] = useState<number | null>(null)

  const loadOptimized = useCallback(async () => {
    setListLoading(true)
    try {
      const res = await resumeApi.list(0, 200)
      if (res.success && res.data?.items) {
        const opt = res.data.items.filter((r) => r.status === 'optimized')
        setOptimizedList(opt)
        setSelectedResumeId((prev) => {
          if (prev != null) return prev
          return opt.length ? opt[0].id : null
        })
      } else {
        setOptimizedList([])
      }
    } catch (e) {
      message.error((e as Error).message)
      setOptimizedList([])
    } finally {
      setListLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadOptimized()
  }, [loadOptimized])

  const handleGenerate = async () => {
    if (selectedResumeId == null) {
      message.warning('请先选择一份已优化完成的简历')
      return
    }
    setGenerating(true)
    try {
      const res = await resumeApi.studyQa(selectedResumeId)
      if (res.success && res.data?.items?.length) {
        setItems(res.data.items)
        setLastSessionId(res.data.session_id)
        message.success('已生成并保存，可在「历史结果 → 学习问答」中查看全部记录')
      } else {
        message.error(res.message || '生成失败')
      }
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setGenerating(false)
    }
  }

  const options = optimizedList.map((r) => ({
    value: r.id,
    label: `${r.original_filename} · #${r.id}${r.target_job_title ? ` · ${r.target_job_title}` : ''}`,
  }))

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <Space align="center" style={{ marginBottom: 24 }}>
        <QuestionCircleOutlined style={{ fontSize: 32, color: 'var(--color-primary)' }} />
        <div>
          <Title level={2} style={{ margin: 0 }}>
            学习问答
          </Title>
          <Paragraph type="secondary" style={{ marginBottom: 0 }}>
            选择一份<strong>已成功优化</strong>的简历，生成面试准备问答；结果会保存，并在历史结果中展示。
          </Paragraph>
        </div>
      </Space>

      <Card style={cardStyle}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Text strong>选择简历</Text>
            <Select
              showSearch
              optionFilterProp="label"
              loading={listLoading}
              placeholder="仅显示「已完成优化」的简历"
              style={{ width: '100%', marginTop: 8 }}
              options={options}
              value={selectedResumeId ?? undefined}
              onChange={(v) => {
                setSelectedResumeId(v)
                setItems([])
                setLastSessionId(null)
              }}
            />
          </div>
          <Space wrap>
            <Button
              type="primary"
              icon={<RocketOutlined />}
              loading={generating}
              onClick={() => void handleGenerate()}
            >
              生成学习问答
            </Button>
            <Link to="/resume/history">
              <Button icon={<HistoryOutlined />}>历史结果（学习问答 Tab）</Button>
            </Link>
            <Link to="/resume">
              <Button type="link">返回简历优化</Button>
            </Link>
          </Space>
          {lastSessionId != null ? (
            <Alert type="success" showIcon message={`本次记录已保存，会话 ID: ${lastSessionId}`} />
          ) : null}
          {items.length > 0 ? (
            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>
                本次生成结果
              </Text>
              <Collapse
                items={items.map((item, idx) => ({
                  key: String(idx),
                  label: (
                    <span>
                      <Tag color="processing" style={{ marginRight: 8 }}>
                        {item.topic}
                      </Tag>
                      {item.question}
                    </span>
                  ),
                  children: (
                    <Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                      {item.answer_hint}
                    </Paragraph>
                  ),
                }))}
              />
            </div>
          ) : (
            <Text type="secondary">生成后在此展开查看每条问答。</Text>
          )}
        </Space>
      </Card>
    </div>
  )
}

export default ResumeStudyQaPage
