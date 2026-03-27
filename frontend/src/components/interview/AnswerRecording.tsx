import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Typography, Progress, Space } from 'antd'
import {
  AudioOutlined,
  CheckCircleOutlined,
  StopOutlined,
} from '@ant-design/icons'

const { Text } = Typography

interface AnswerRecordingProps {
  isRecording: boolean
  duration: number // 当前录音时长（秒）
  maxDuration?: number // 最大录音时长（秒）
  waveform?: number[] // 波形数据 (0-1 之间的数组)
  status?: 'recording' | 'paused' | 'completed' | 'error'
  onToggle?: () => void
  showTimer?: boolean
  compact?: boolean
}

/**
 * 录音状态显示组件
 * 展示录音中的状态、时长和波形动画
 */
export const AnswerRecording: React.FC<AnswerRecordingProps> = ({
  isRecording,
  duration,
  maxDuration = 120, // 默认 2 分钟
  waveform,
  status = 'recording',
  onToggle,
  showTimer = true,
  compact = false,
}) => {
  const [progress, setProgress] = useState(0)
  const [displayWaveform, setDisplayWaveform] = useState<number[]>([])

  // 计算进度百分比
  useEffect(() => {
    const percent = Math.min((duration / maxDuration) * 100, 100)
    setProgress(percent)
  }, [duration, maxDuration])

  // 模拟波形动画（如果没有传入真实波形数据）
  useEffect(() => {
    if (!isRecording) {
      setDisplayWaveform([])
      return
    }

    const interval = setInterval(() => {
      if (waveform) {
        setDisplayWaveform(waveform)
      } else {
        // 生成随机波形
        const bars = 20
        const newWaveform = Array.from(
          { length: bars },
          () => Math.random() * 0.8 + 0.2
        )
        setDisplayWaveform(newWaveform)
      }
    }, 150)

    return () => clearInterval(interval)
  }, [isRecording, waveform])

  // 格式化时间显示
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // 状态配置
  const statusConfig = {
    recording: {
      icon: <AudioOutlined />,
      text: '正在录音...',
      color: '#ff4d4f',
      pulse: true,
    },
    paused: {
      icon: <StopOutlined />,
      text: '已暂停',
      color: '#faad14',
      pulse: false,
    },
    completed: {
      icon: <CheckCircleOutlined />,
      text: '录音完成',
      color: '#52c41a',
      pulse: false,
    },
    error: {
      icon: <StopOutlined />,
      text: '录音失败',
      color: '#ff4d4f',
      pulse: false,
    },
  }

  const config = statusConfig[status]

  return (
    <div
      style={{
        padding: compact ? '12px' : '20px',
        background: '#fafafa',
        borderRadius: 8,
        border: `2px solid ${config.color}`,
        textAlign: 'center',
      }}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {/* 状态图标和文字 */}
        <div style={{ position: 'relative', display: 'inline-block', margin: '0 auto' }}>
          {config.pulse && (
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 0, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              style={{
                position: 'absolute',
                top: -10,
                left: -10,
                right: -10,
                bottom: -10,
                borderRadius: '50%',
                background: config.color,
                zIndex: 0,
              }}
            />
          )}
          <motion.div
            animate={
              config.pulse
                ? { scale: [1, 1.1, 1] }
                : { scale: 1 }
            }
            transition={{
              duration: 0.5,
              repeat: config.pulse ? Infinity : 0,
            }}
            style={{
              fontSize: compact ? 32 : 48,
              color: config.color,
              position: 'relative',
              zIndex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {config.icon}
          </motion.div>
        </div>

        <Text
          strong
          style={{
            fontSize: compact ? 14 : 16,
            color: config.color,
            display: 'block',
          }}
        >
          {config.text}
        </Text>

        {/* 计时器 */}
        {showTimer && (
          <div>
            <Text
              style={{
                fontSize: compact ? 24 : 32,
                fontFamily: 'monospace',
                fontWeight: 'bold',
                color: '#333',
              }}
            >
              {formatTime(duration)}
            </Text>
            <Text
              type="secondary"
              style={{ fontSize: 12, marginLeft: 8 }}
            >
              / {formatTime(maxDuration)}
            </Text>
          </div>
        )}

        {/* 进度条 */}
        <Progress
          percent={progress}
          strokeColor={progress > 90 ? '#ff4d4f' : '#1890ff'}
          trailColor="#f0f0f0"
          showInfo={false}
          size={compact ? 'small' : 'default'}
        />

        {/* 波形可视化 */}
        {isRecording && displayWaveform.length > 0 && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 3,
              height: 40,
              marginTop: 8,
            }}
          >
            {displayWaveform.map((value, index) => (
              <motion.div
                key={index}
                animate={{
                  height: [value * 20, value * 40, value * 20],
                }}
                transition={{
                  duration: 0.3,
                  repeat: Infinity,
                  delay: index * 0.05,
                }}
                style={{
                  width: 4,
                  backgroundColor: config.color,
                  borderRadius: 2,
                }}
              />
            ))}
          </div>
        )}

        {/* 控制按钮 */}
        {onToggle && (
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onToggle}
            style={{
              padding: '8px 24px',
              fontSize: 14,
              borderRadius: 20,
              border: 'none',
              background: isRecording ? '#ff4d4f' : '#1890ff',
              color: 'white',
              cursor: 'pointer',
              fontWeight: 500,
              marginTop: 8,
            }}
          >
            {isRecording ? '停止录音' : '开始录音'}
          </motion.button>
        )}
      </Space>
    </div>
  )
}

export default AnswerRecording
