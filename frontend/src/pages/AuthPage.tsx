// Login & Register Page - 登录注册页面

import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, message, Tabs } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';

const { Title } = Typography;

interface AuthFormProps {
  onLogin: (token: string, user: any) => void;
}

const AuthPage: React.FC<AuthFormProps> = ({ onLogin }) => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const res = await authApi.login(values.email, values.password);
      localStorage.setItem('token', res.access_token);
      localStorage.setItem('user', JSON.stringify(res.user));
      onLogin(res.access_token, res.user);
      message.success('登录成功');
      navigate('/');
    } catch (err: any) {
      message.error(err.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: {
    email: string;
    password: string;
    username?: string;
    phone?: string;
  }) => {
    setLoading(true);
    try {
      const res = await authApi.register(values);
      localStorage.setItem('token', res.access_token);
      localStorage.setItem('user', JSON.stringify(res.user));
      onLogin(res.access_token, res.user);
      message.success('注册成功');
      navigate('/');
    } catch (err: any) {
      message.error(err.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  const tabItems = [
    {
      key: 'login',
      label: '登录',
      children: (
        <Form onFinish={handleLogin} size="large">
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登录
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'register',
      label: '注册',
      children: (
        <Form onFinish={handleRegister} size="large">
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" />
          </Form.Item>
          <Form.Item name="username">
            <Input prefix={<UserOutlined />} placeholder="用户名（选填）" />
          </Form.Item>
          <Form.Item name="phone">
            <Input prefix={<PhoneOutlined />} placeholder="手机号（选填）" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请设置密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码（至少6位）" />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              注册
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card style={{ width: 420, boxShadow: '0 8px 32px rgba(0,0,0,0.15)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3} style={{ margin: 0, color: '#6366f1' }}>
            AI 求职助手
          </Title>
          <p style={{ color: '#888', marginTop: 8 }}>
            简历优化 · 面试模拟 · 智能求职
          </p>
        </div>
        <Tabs items={tabItems} centered />
      </Card>
    </div>
  );
};

export default AuthPage;
