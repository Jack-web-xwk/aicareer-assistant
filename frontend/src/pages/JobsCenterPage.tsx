import { useState } from 'react'
import { Tabs } from 'antd'
import JobsPage from './JobsPage'
import SavedJobsPage from './SavedJobsPage'
import TargetJobUrlPage from './TargetJobUrlPage'

export default function JobsCenterPage() {
  const [activeTab, setActiveTab] = useState<string>('search')

  const tabItems: Array<{
    key: string
    label: string
    children: React.ReactNode
  }> = [
    {
      key: 'search',
      label: '职位搜索',
      children: <JobsPage />,
    },
    {
      key: 'saved',
      label: '我的职位',
      children: <SavedJobsPage />,
    },
    {
      key: 'target',
      label: '目标岗位',
      children: <TargetJobUrlPage />,
    },
  ]

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="large"
        style={{ marginBottom: 24 }}
      />
    </div>
  )
}
