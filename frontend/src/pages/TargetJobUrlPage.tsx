import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Input,
  Space,
  Spin,
  Tag,
  Typography,
  message,
} from 'antd'
import { LinkOutlined, SearchOutlined, FolderOpenOutlined } from '@ant-design/icons'

import { jobScrapeApi } from '../services/api'
import type { SavedJobRecord } from '../types'

const { Title, Paragraph, Text } = Typography

export default function TargetJobUrlPage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState<SavedJobRecord | null>(null)
  const [snapshot, setSnapshot] = useState<Record<string, unknown> | null>(null)

  const handleScrape = async () => {
    const u = url.trim()
    if (!u) {
      message.warning('请输入岗位详情页链接')
      return
    }
    setLoading(true)
    setSaved(null)
    setSnapshot(null)
    try {
      const res = await jobScrapeApi.scrapeAndSave(u)
      if (!res.success || !res.data) {
        message.error(res.message || '请求失败')
        return
      }
      const data = res.data as {
        saved: SavedJobRecord
        job_snapshot: Record<string, unknown>
      }
      setSaved(data.saved)
      setSnapshot(data.job_snapshot)
      message.success('已爬取并保存到「我的职位」')
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={3} style={{ marginBottom: 8 }}>
            目标岗位（链接爬取）
          </Title>
          <Paragraph type="secondary">
            粘贴招聘网站<strong>岗位详情页</strong>的 URL（如 Boss 直聘 job_detail 页面），系统将自动爬取岗位信息并
            <strong>持久化保存</strong>到数据库，可在「我的职位」中查看，也可用于「简历优化」。
          </Paragraph>
          <Alert
            type="info"
            showIcon
            style={{ marginTop: 12 }}
            message="与「职位搜索」区别：此处为单链接爬取入库，不是多源关键词列表搜索。"
          />
        </div>

        <Card>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Text strong>岗位详情页 URL</Text>
            <Input.Search
              size="large"
              placeholder="https://www.zhipin.com/job_detail/xxxx.html"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onSearch={() => void handleScrape()}
              enterButton={
                <span>
                  <SearchOutlined /> 爬取并保存
                </span>
              }
              loading={loading}
            />
            <Space wrap>
              <Link to="/jobs/saved">
                <Button icon={<FolderOpenOutlined />}>我的职位</Button>
              </Link>
              <Link to="/jobs">
                <Button>多源职位搜索</Button>
              </Link>
            </Space>
          </Space>
        </Card>

        <Spin spinning={loading}>
          {saved ? (
            <Card title="已保存摘要" extra={<Tag color="green">入库成功</Tag>}>
              <Descriptions column={1} size="small" bordered>
                <Descriptions.Item label="职位">{saved.title}</Descriptions.Item>
                <Descriptions.Item label="公司">{saved.company_name || '—'}</Descriptions.Item>
                <Descriptions.Item label="薪资">{saved.salary_text || '—'}</Descriptions.Item>
                <Descriptions.Item label="地点">{saved.location || '—'}</Descriptions.Item>
                <Descriptions.Item label="链接">
                  <a href={saved.detail_url} target="_blank" rel="noopener noreferrer">
                    {saved.detail_url} <LinkOutlined />
                  </a>
                </Descriptions.Item>
              </Descriptions>
              <Space style={{ marginTop: 16 }}>
                <Link to={`/resume?targetJobUrl=${encodeURIComponent(saved.detail_url)}`}>
                  <Button type="primary">用于简历优化</Button>
                </Link>
              </Space>
            </Card>
          ) : null}

          {snapshot && !loading ? (
            <Card title="爬取到的结构化字段（节选）" size="small">
              <Paragraph type="secondary" style={{ fontSize: 12 }}>
                完整 JSON 已写入数据库 raw_snippet 字段。
              </Paragraph>
              <pre
                style={{
                  maxHeight: 320,
                  overflow: 'auto',
                  fontSize: 12,
                  background: 'var(--color-bg-secondary)',
                  padding: 12,
                  borderRadius: 8,
                }}
              >
                {JSON.stringify(snapshot, null, 2)}
              </pre>
            </Card>
          ) : null}
        </Spin>
      </Space>
    </div>
  )
}
