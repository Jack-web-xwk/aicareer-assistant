import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Layout, Menu, Typography } from 'antd'
import {
  FileTextOutlined,
  AudioOutlined,
  HomeOutlined,
  RocketOutlined,
  HistoryOutlined,
  SearchOutlined,
  AimOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons'
import HomePage from './pages/HomePage'
import ResumeOptimizerPage from './pages/ResumeOptimizerPage'
import ResumeHistoryPage from './pages/ResumeHistoryPage'
import InterviewSimulatorPage from './pages/InterviewSimulatorPage'
import JobsPage from './pages/JobsPage'
import SavedJobsPage from './pages/SavedJobsPage'
import TargetJobUrlPage from './pages/TargetJobUrlPage'

const { Header, Content, Footer } = Layout
const { Title } = Typography

function menuSelectedKey(pathname: string): string {
  if (pathname.startsWith('/resume/history')) return '/resume/history'
  if (pathname.startsWith('/target-jobs')) return '/target-jobs'
  if (pathname.startsWith('/jobs/saved')) return '/jobs/saved'
  if (pathname.startsWith('/jobs')) return '/jobs'
  if (pathname.startsWith('/resume')) return '/resume'
  return pathname
}

function AppLayout() {
  const location = useLocation()
  
  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: '/jobs',
      icon: <SearchOutlined />,
      label: <Link to="/jobs">职位搜索</Link>,
    },
    {
      key: '/target-jobs',
      icon: <AimOutlined />,
      label: <Link to="/target-jobs">目标岗位</Link>,
    },
    {
      key: '/jobs/saved',
      icon: <FolderOpenOutlined />,
      label: <Link to="/jobs/saved">我的职位</Link>,
    },
    {
      key: '/resume',
      icon: <FileTextOutlined />,
      label: <Link to="/resume">简历优化</Link>,
    },
    {
      key: '/resume/history',
      icon: <HistoryOutlined />,
      label: <Link to="/resume/history">历史结果</Link>,
    },
    {
      key: '/interview',
      icon: <AudioOutlined />,
      label: <Link to="/interview">面试模拟</Link>,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          padding: '0 48px',
          background: '#ffffff',
          borderBottom: '1px solid var(--color-border)',
          boxShadow: 'var(--shadow-sm)',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <RocketOutlined style={{ fontSize: '28px', color: '#6366f1' }} />
          <Title
            level={4}
            style={{
              margin: 0,
              background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            AI 求职助手
          </Title>
        </div>
        <Menu
          mode="horizontal"
          selectedKeys={[menuSelectedKey(location.pathname)]}
          items={menuItems}
          style={{
            flex: 1,
            minWidth: 0,
            background: 'transparent',
            borderBottom: 'none',
            marginLeft: '48px',
          }}
        />
      </Header>
      
      <Content
        style={{
          padding: '24px 48px',
          minHeight: 'calc(100vh - 134px)',
          background: 'var(--color-bg-primary)',
        }}
      >
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/jobs/saved" element={<SavedJobsPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/target-jobs" element={<TargetJobUrlPage />} />
          <Route path="/resume/history" element={<ResumeHistoryPage />} />
          <Route path="/resume" element={<ResumeOptimizerPage />} />
          <Route path="/interview" element={<InterviewSimulatorPage />} />
        </Routes>
      </Content>
      
      <Footer
        style={{
          textAlign: 'center',
          background: 'transparent',
          color: 'var(--color-text-muted)',
          borderTop: '1px solid var(--color-border)',
        }}
      >
        AI Career Assistant ©{new Date().getFullYear()} - Powered by FastAPI + LangGraph
      </Footer>
    </Layout>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}

export default App
