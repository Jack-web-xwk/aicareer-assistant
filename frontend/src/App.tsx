import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom'
import { Layout, Menu, Typography, Dropdown, Avatar, message } from 'antd'
import {
  FileTextOutlined,
  AudioOutlined,
  HomeOutlined,
  RocketOutlined,
  HistoryOutlined,
  SearchOutlined,
  ReadOutlined,
  UserOutlined,
  LogoutOutlined,
  GithubOutlined,
} from '@ant-design/icons'
import { useState, useEffect } from 'react'
import HomePage from './pages/HomePage'
import ResumeOptimizerPage from './pages/ResumeOptimizerPage'
import ResumeHistoryPage from './pages/ResumeHistoryPage'
import InterviewSimulatorPage from './pages/InterviewSimulatorPage'
import JobsCenterPage from './pages/JobsCenterPage'
import LearnPage from './pages/LearnPage'
import AuthPage from './pages/AuthPage'
import OnboardingGuide from './components/OnboardingGuide'

const { Header, Content, Footer } = Layout
const { Title } = Typography

interface UserInfo {
  id: number
  email: string
  username?: string
  avatar_url?: string
}

function menuSelectedKey(pathname: string): string {
  if (pathname.startsWith('/learn')) return '/learn'
  if (pathname.startsWith('/history')) return '/history'
  if (pathname.startsWith('/interview')) return '/interview'
  if (pathname.startsWith('/resume')) return '/resume'
  if (pathname.startsWith('/jobs')) return '/jobs'
  return pathname
}

// 受保护路由：未登录跳转到 /auth
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  if (!token) {
    return <Navigate to="/auth" replace />
  }
  return <>{children}</>
}

function AppLayout() {
  const location = useLocation()
  const [user, setUser] = useState<UserInfo | null>(null)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (savedToken) setToken(savedToken)
    if (savedUser) {
      try { setUser(JSON.parse(savedUser)) } catch {}
    }
  }, [])

  // 路由变化时重新检查 token
  useEffect(() => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    setToken(savedToken)
    if (savedUser) {
      try { setUser(JSON.parse(savedUser)) } catch {}
    }
  }, [location.pathname])

  const handleLogin = (newToken: string, newUser: any) => {
    setToken(newToken)
    setUser(newUser)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    message.success('已退出登录')
  }

  // 登录/注册页
  if (location.pathname === '/auth') {
    return <AuthPage onLogin={handleLogin} />
  }

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: '/jobs',
      icon: <SearchOutlined />,
      label: <Link to="/jobs">职位中心</Link>,
    },
    {
      key: '/resume',
      icon: <FileTextOutlined />,
      label: <Link to="/resume">简历优化</Link>,
    },
    {
      key: '/interview',
      icon: <AudioOutlined />,
      label: <Link to="/interview">面试模拟</Link>,
    },
    {
      key: '/learn',
      icon: <ReadOutlined />,
      label: <Link to="/learn">学习中心</Link>,
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: <Link to="/history">历史结果</Link>,
    },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: user?.username || user?.email || '用户',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Menu
            mode="horizontal"
            selectedKeys={[menuSelectedKey(location.pathname)]}
            items={menuItems}
            style={{
              flex: 1,
              minWidth: 0,
              background: 'transparent',
              borderBottom: 'none',
            }}
          />
          <a
            href="https://github.com/Jack-web-xwk/aicareer-assistant"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '20px',
              color: '#6366f1',
              cursor: 'pointer',
              transition: 'color 0.3s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#8b5cf6')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#6366f1')}
          >
            <GithubOutlined />
          </a>
          {token && (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Avatar
                icon={<UserOutlined />}
                style={{ backgroundColor: '#6366f1', cursor: 'pointer' }}
                src={user?.avatar_url}
              />
            </Dropdown>
          )}
        </div>
      </Header>

      <Content
        style={{
          padding: '24px 48px',
          minHeight: 'calc(100vh - 134px)',
          background: 'var(--color-bg-primary)',
        }}
      >
        <Routes>
          <Route path="/auth" element={<AuthPage onLogin={handleLogin} />} />
          <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
          <Route path="/jobs" element={<ProtectedRoute><JobsCenterPage /></ProtectedRoute>} />
          <Route path="/resume/history" element={<ProtectedRoute><ResumeHistoryPage /></ProtectedRoute>} />
          <Route path="/resume/study-qa" element={<ProtectedRoute><Navigate to="/learn" replace /></ProtectedRoute>} />
          <Route path="/resume" element={<ProtectedRoute><ResumeOptimizerPage /></ProtectedRoute>} />
          <Route path="/learn" element={<ProtectedRoute><LearnPage /></ProtectedRoute>} />
          <Route path="/interview" element={<ProtectedRoute><InterviewSimulatorPage /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><ResumeHistoryPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
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
      {/* 用户首次访问引导 */}
      <OnboardingGuide />
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
