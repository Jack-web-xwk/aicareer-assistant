import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Alert,
  Button,
  Card,
  Descriptions,
  Divider,
  Input,
  Space,
  Spin,
  Tag,
  Typography,
  Upload,
  message,
} from 'antd'
import type { UploadFile } from 'antd/es/upload/interface'
import {
  LinkOutlined,
  SearchOutlined,
  FolderOpenOutlined,
  PictureOutlined,
  CloudUploadOutlined,
} from '@ant-design/icons'

import { jobScrapeApi } from '../services/api'
import type { SavedJobRecord } from '../types'

const { Title, Paragraph, Text } = Typography
const { Dragger } = Upload

function isScreenshotJob(detailUrl: string) {
  return detailUrl.startsWith('job:screenshot:')
}

export default function TargetJobUrlPage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [saved, setSaved] = useState<SavedJobRecord | null>(null)
  const [snapshot, setSnapshot] = useState<Record<string, unknown> | null>(null)
  const [fileList, setFileList] = useState<UploadFile[]>([])

  const resetResult = () => {
    setSaved(null)
    setSnapshot(null)
  }

  /** 剪贴板粘贴图片（Ctrl+V）→ 填入上传列表，与拖拽/点击选图共用同一套上传逻辑 */
  const onPasteClipboardImage = useCallback(
    (e: ClipboardEvent) => {
      if (loading) return
      const items = e.clipboardData?.items
      if (!items?.length) return
      
      const imageFiles: UploadFile[] = []
      
      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        if (item.kind === 'file' && item.type.startsWith('image/')) {
          const blob = item.getAsFile()
          if (!blob) continue
          e.preventDefault()
          const sub = blob.type.split('/')[1]?.replace('jpeg', 'jpg') || 'png'
          const file = new File([blob], `paste-${Date.now()}-${i}.${sub}`, {
            type: blob.type || 'image/png',
          })
          imageFiles.push({
            uid: `paste-${Date.now()}-${i}`,
            name: file.name,
            status: 'done',
            originFileObj: file as unknown as UploadFile['originFileObj'],
          })
        }
      }
      
      if (imageFiles.length > 0) {
        // 追加到现有文件列表，支持同时粘贴多张图片
        setFileList((prev) => [...prev, ...imageFiles])
        message.success(`已粘贴 ${imageFiles.length} 张截图，可点击「识别截图并保存」`)
      }
    },
    [loading]
  )

  useEffect(() => {
    document.addEventListener('paste', onPasteClipboardImage)
    return () => document.removeEventListener('paste', onPasteClipboardImage)
  }, [onPasteClipboardImage])

  const handleScrape = async () => {
    const u = url.trim()
    if (!u) {
      message.warning('请输入岗位详情页链接')
      return
    }
    setLoading(true)
    resetResult()
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

  const handleScreenshotUpload = async () => {
    const files = fileList
      .map((f) => f.originFileObj as File | undefined)
      .filter((f): f is File => !!f)
    
    if (!files.length) {
      message.warning('请先选择至少一张截图')
      return
    }
    setLoading(true)
    resetResult()
    try {
      const res = await jobScrapeApi.fromScreenshot(files)
      if (!res.success || !res.data) {
        message.error(res.message || '请求失败')
        return
      }
      const data = res.data as {
        saved: SavedJobRecord
        job_snapshot: Record<string, unknown>
        uploaded_count: number
      }
      setSaved(data.saved)
      setSnapshot(data.job_snapshot)
      setFileList([])
      message.success(`已从 ${data.uploaded_count} 张截图中识别并保存到「我的职位」`)
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const resumeOptimizeHref = saved
    ? `/resume?targetJobUrl=${encodeURIComponent(saved.detail_url)}`
    : '#'

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={3} style={{ marginBottom: 8 }}>
            目标岗位
          </Title>
          <Paragraph type="secondary">
            下面两种<strong>同时展示在页面中</strong>，任选其一：粘贴链接由服务端爬取，或上传/粘贴截图由多模态模型识别；结果都会
            <strong>保存到「我的职位」</strong>，供简历优化使用。
          </Paragraph>
          <Alert
            type="info"
            showIcon
            style={{ marginTop: 12 }}
            message={
              <span>
                截图识别需后端配置视觉模型 API（如通义 qwen-image-edit-plus、智谱 glm-4v 等）。
                若关注「任意链接 → 稳定抽正文」的通用方案，可参考{' '}
                <a
                  href="https://mp.weixin.qq.com/s/ljMffydOigAl1muyLFhQhw"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  这篇说明
                </a>
                （Jina / Scrapling 等分层思路；与本项目 Boss 专用爬取并存）。
              </span>
            }
          />
        </div>

        <Spin spinning={loading}>
          <Card
            title={
              <Space>
                <LinkOutlined />
                <span>方式一：粘贴岗位详情页链接</span>
                <Tag color="blue">爬取</Tag>
              </Space>
            }
          >
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
                disabled={loading}
              />
            </Space>
          </Card>

          <Divider plain>
            <Text type="secondary">或</Text>
          </Divider>

          <Card
            title={
              <Space>
                <PictureOutlined />
                <span>方式二：上传详情页截图（多模态识别）</span>
                <Tag color="purple">截图</Tag>
              </Space>
            }
            style={{ borderColor: 'var(--color-border, #e5e7eb)' }}
            styles={{
              header: { background: 'rgba(139, 92, 246, 0.06)' },
            }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                请截取包含<strong>职位名称、公司、薪资、工作地点、职位描述</strong>的页面；支持 PNG / JPEG / WebP。
                在本页任意位置按 <strong>Ctrl+V</strong>（Mac：⌘+V）可粘贴剪贴板中的截图，无需先保存为文件。
              </Paragraph>
              <Dragger
                accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
                multiple
                fileList={fileList}
                beforeUpload={() => false}
                onChange={({ fileList: fl }) => setFileList(fl)}
                disabled={loading}
              >
                <p className="ant-upload-drag-icon">
                  <CloudUploadOutlined style={{ color: '#8b5cf6' }} />
                </p>
                <p className="ant-upload-text">点击或拖拽图片到此处</p>
                <p className="ant-upload-hint">
                  支持多张图片同时上传，建议竖屏长截图包含完整 JD；也可在页面按 Ctrl+V 粘贴
                </p>
              </Dragger>
              <Button
                type="primary"
                icon={<PictureOutlined />}
                onClick={() => void handleScreenshotUpload()}
                loading={loading}
                disabled={!fileList.length || loading}
                style={{ background: '#7c3aed', borderColor: '#7c3aed' }}
              >
                识别截图并保存
              </Button>
            </Space>
          </Card>
        </Spin>

        <Card size="small">
          <Space wrap>
            <Link to="/jobs/saved">
              <Button icon={<FolderOpenOutlined />}>我的职位</Button>
            </Link>
            <Link to="/jobs">
              <Button>多源职位搜索</Button>
            </Link>
          </Space>
        </Card>

        <Spin spinning={loading}>
          {saved ? (
            <Card title="已保存摘要" extra={<Tag color="green">入库成功</Tag>}>
              <Descriptions column={1} size="small" bordered>
                <Descriptions.Item label="来源">
                  {saved.source === 'screenshot' ? (
                    <Tag color="purple">截图识别</Tag>
                  ) : (
                    <Tag>链接爬取</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="职位">{saved.title}</Descriptions.Item>
                <Descriptions.Item label="公司">{saved.company_name || '—'}</Descriptions.Item>
                <Descriptions.Item label="薪资">{saved.salary_text || '—'}</Descriptions.Item>
                <Descriptions.Item label="地点">{saved.location || '—'}</Descriptions.Item>
                <Descriptions.Item label="关联标识">
                  {isScreenshotJob(saved.detail_url) ? (
                    <Text type="secondary" code copyable>
                      {saved.detail_url}
                    </Text>
                  ) : (
                    <a href={saved.detail_url} target="_blank" rel="noopener noreferrer">
                      {saved.detail_url} <LinkOutlined />
                    </a>
                  )}
                </Descriptions.Item>
              </Descriptions>
              <Space style={{ marginTop: 16 }}>
                <Link to={resumeOptimizeHref}>
                  <Button type="primary">用于简历优化</Button>
                </Link>
                {saved.source === 'screenshot' ? (
                  <Link to={`/resume?savedJobId=${saved.id}`}>
                    <Button>打开优化页（按保存 ID）</Button>
                  </Link>
                ) : null}
              </Space>
            </Card>
          ) : null}

          {snapshot && !loading ? (
            <Card title="结构化字段（节选）" size="small">
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
