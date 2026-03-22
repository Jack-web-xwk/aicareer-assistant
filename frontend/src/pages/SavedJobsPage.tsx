import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Button,
  Card,
  Col,
  Empty,
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
  LinkOutlined,
  RocketOutlined,
} from '@ant-design/icons'

import { jobSavedApi } from '../services/api'
import type { JobSource, SavedJobRecord } from '../types'

const { Title, Text } = Typography

const SOURCE_LABEL: Record<JobSource, string> = {
  boss: 'Boss直聘',
  zhaopin: '智联招聘',
  yupao: '鱼泡',
  link: '链接爬取',
}

const SOURCE_COLOR: Record<JobSource, string> = {
  boss: 'blue',
  zhaopin: 'green',
  yupao: 'orange',
  link: 'purple',
}

export default function SavedJobsPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState<SavedJobRecord[]>([])
  const [total, setTotal] = useState(0)

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
      render: (_, r) => (
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
