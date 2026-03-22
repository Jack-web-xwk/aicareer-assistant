import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Col,
  Divider,
  Empty,
  List,
  Modal,
  Popconfirm,
  Row,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  BankOutlined,
  DeleteOutlined,
  EnvironmentOutlined,
  EyeOutlined,
  LinkOutlined,
  RocketOutlined,
} from '@ant-design/icons'

import { jobSavedApi } from '../services/api'
import type { JobSnapshot, JobSource, SavedJobRecord } from '../types'

const { Title, Text } = Typography

function parseJobSnapshot(raw: string | null | undefined): JobSnapshot | null {
  if (!raw?.trim()) return null
  try {
    return JSON.parse(raw) as JobSnapshot
  } catch {
    return null
  }
}

function JobDetailBody({
  record,
  detail,
}: {
  record: SavedJobRecord
  detail: JobSnapshot | null
}) {
  const showLink = !record.detail_url.startsWith('job:screenshot:')
  if (!detail) {
    return (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Text type="secondary">暂无结构化详情（旧数据或未写入 raw_snippet）。</Text>
        {showLink ? (
          <a href={record.detail_url} target="_blank" rel="noopener noreferrer">
            打开原职位页 <LinkOutlined />
          </a>
        ) : null}
      </Space>
    )
  }

  const tagBlock = (label: string, items: string[] | undefined) =>
    items && items.length > 0 ? (
      <div>
        <Text strong>{label}</Text>
        <div style={{ marginTop: 8 }}>
          <Space wrap size={[4, 8]}>
            {items.map((t, i) => (
              <Tag key={`${t}-${i}`}>{t}</Tag>
            ))}
          </Space>
        </div>
      </div>
    ) : null

  const listBlock = (label: string, items: string[] | undefined) =>
    items && items.length > 0 ? (
      <>
        <Title level={5} style={{ marginTop: 0, marginBottom: 8 }}>
          {label}
        </Title>
        <List
          size="small"
          dataSource={items}
          renderItem={(line) => <List.Item style={{ padding: '4px 0' }}>{line}</List.Item>}
        />
      </>
    ) : null

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {showLink ? (
        <a href={record.detail_url} target="_blank" rel="noopener noreferrer">
          打开原职位页 <LinkOutlined />
        </a>
      ) : (
        <Text type="secondary">截图保存岗位（无外链），以下为识别结果</Text>
      )}

      <div>
        <Title level={4} style={{ marginBottom: 4 }}>
          {detail.title || record.title}
        </Title>
        <Space wrap split={<Divider type="vertical" />}>
          <Text>
            <BankOutlined /> {(detail.company ?? record.company_name) || '—'}
          </Text>
          <Text type="secondary">{(detail.salary ?? record.salary_text) || '—'}</Text>
          <Text type="secondary">
              <EnvironmentOutlined /> {(detail.location ?? record.location) || '—'}
          </Text>
        </Space>
      </div>

      <Space wrap split={<Divider type="vertical" />}>
        {detail.industry ? <Tag>{detail.industry}</Tag> : null}
        {detail.company_scale ? <Tag>规模 {detail.company_scale}</Tag> : null}
        {detail.financing_stage ? <Tag>{detail.financing_stage}</Tag> : null}
        {detail.experience_years ? <Tag>经验 {detail.experience_years}</Tag> : null}
        {detail.education_requirement ? <Tag>学历 {detail.education_requirement}</Tag> : null}
      </Space>

      {tagBlock('技能标签', detail.tech_stack_tags)}
      {tagBlock('福利', detail.benefits)}

      {listBlock('岗位职责', detail.responsibilities)}
      {listBlock('任职要求', detail.qualifications)}

      {listBlock('必备能力（正文提炼）', detail.required_skills)}
      {listBlock('加分项', detail.preferred_skills)}

      {(detail.work_address || detail.work_schedule) && (
        <>
          <Divider plain style={{ margin: '8px 0' }} />
          {detail.work_address ? (
            <Text>
              <strong>办公地址：</strong>
              {detail.work_address}
            </Text>
          ) : null}
          {detail.work_schedule ? (
            <div>
              <Text>
                <strong>工作时间：</strong>
                {detail.work_schedule}
              </Text>
            </div>
          ) : null}
        </>
      )}

      {(detail.recruiter_name || detail.recruiter_title) && (
        <div>
          <Text strong>招聘方</Text>
          <div style={{ marginTop: 4 }}>
            <Text>
              {[detail.recruiter_name, detail.recruiter_title].filter(Boolean).join(' · ')}
            </Text>
          </div>
        </div>
      )}
    </Space>
  )
}

const SOURCE_LABEL: Record<JobSource, string> = {
  boss: 'Boss直聘',
  zhaopin: '智联招聘',
  yupao: '鱼泡',
  link: '链接爬取',
  screenshot: '截图识别',
}

const SOURCE_COLOR: Record<JobSource, string> = {
  boss: 'blue',
  zhaopin: 'green',
  yupao: 'orange',
  link: 'purple',
  screenshot: 'magenta',
}

export default function SavedJobsPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<SavedJobRecord[]>([])
  const [total, setTotal] = useState(0)
  const [detailRecord, setDetailRecord] = useState<SavedJobRecord | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await jobSavedApi.list(0, 100)
      if (res.success && res.data) {
        setItems(res.data.items)
        setTotal(res.data.total)
      } else {
        message.error(res.message || '加载失败')
      }
    } catch (e) {
      message.error((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handleDelete = async (id: number) => {
    try {
      const res = await jobSavedApi.delete(id)
      if (res.success) {
        message.success('已删除')
        void load()
      } else {
        message.error(res.message || '删除失败')
      }
    } catch (e) {
      message.error((e as Error).message)
    }
  }

  const columns: ColumnsType<SavedJobRecord> = [
    {
      title: '职位',
      key: 'title',
      render: (_, r) =>
        r.source === 'screenshot' || r.detail_url.startsWith('job:screenshot:') ? (
          <Text strong>{r.title}</Text>
        ) : (
          <a href={r.detail_url} target="_blank" rel="noopener noreferrer">
            {r.title} <LinkOutlined />
          </a>
        ),
    },
    {
      title: '公司',
      key: 'company',
      render: (_, r) => (
        <Text>
          <BankOutlined /> {r.company_name || '—'}
        </Text>
      ),
    },
    {
      title: '地点 / 薪资',
      key: 'loc',
      render: (_, r) => (
        <Text type="secondary">
          <EnvironmentOutlined /> {r.location || '—'} · {r.salary_text || '—'}
        </Text>
      ),
    },
    {
      title: '来源',
      dataIndex: 'source',
      width: 100,
      render: (s: JobSource) => (
        <Tag color={SOURCE_COLOR[s]}>{SOURCE_LABEL[s]}</Tag>
      ),
    },
    {
      title: '保存时间',
      dataIndex: 'updated_at',
      width: 180,
      render: (t: string) => <Text type="secondary">{t?.replace('T', ' ').slice(0, 19)}</Text>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_, r) => (
        <Space wrap>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => setDetailRecord(r)}
          >
            查看详细
          </Button>
          <Button
            type="primary"
            size="small"
            icon={<RocketOutlined />}
            onClick={() =>
              navigate(`/resume?targetJobUrl=${encodeURIComponent(r.detail_url)}`)
            }
          >
            简历优化
          </Button>
          <Popconfirm title="确定删除？" onConfirm={() => void handleDelete(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ marginBottom: 4 }}>
              我的保存职位
            </Title>
            <Text type="secondary">
              共 {total} 条 · 数据保存在服务端数据库
            </Text>
          </Col>
          <Col>
            <Space>
              <Link to="/target-jobs">
                <Button type="primary">去搜索岗位</Button>
              </Link>
              <Button onClick={() => void load()}>刷新</Button>
            </Space>
          </Col>
        </Row>

        <Modal
          title="职位详情"
          open={detailRecord !== null}
          onCancel={() => setDetailRecord(null)}
          footer={null}
          width={720}
          destroyOnClose
        >
          {detailRecord ? (
            <JobDetailBody
              record={detailRecord}
              detail={parseJobSnapshot(detailRecord.raw_snippet)}
            />
          ) : null}
        </Modal>

        <Card>
          <Spin spinning={loading}>
            {items.length === 0 && !loading ? (
              <Empty description="暂无保存的职位">
                <Link to="/target-jobs">
                  <Button type="primary">前往目标岗位搜索</Button>
                </Link>
              </Empty>
            ) : (
              <Table<SavedJobRecord>
                rowKey="id"
                columns={columns}
                dataSource={items}
                pagination={false}
                scroll={{ x: 900 }}
              />
            )}
          </Spin>
        </Card>
      </Space>
    </div>
  )
}
