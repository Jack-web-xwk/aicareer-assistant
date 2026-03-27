import React, { useMemo } from 'react'
import { Card, Typography, Space, Tooltip } from 'antd'
import { CalendarOutlined } from '@ant-design/icons'
import type { HeatmapData } from '../../types'

const { Text } = Typography

interface HeatmapCalendarProps {
  activityData: HeatmapData
  month?: string
  title?: string
  compact?: boolean
  onDayClick?: (date: string) => void
}

/**
 * 热力图组件
 * 展示练习活动的日历热力图（类似 GitHub contributions）
 */
export const HeatmapCalendar: React.FC<HeatmapCalendarProps> = ({
  activityData,
  month,
  title,
  compact = false,
  onDayClick,
}) => {
  // 颜色强度映射（从浅到深）
  const getColorByIntensity = (intensity: number): string => {
    if (intensity === 0) return '#f6f8fa'
    if (intensity < 0.25) return '#9be9a8'
    if (intensity < 0.5) return '#40c463'
    if (intensity < 0.75) return '#30a14e'
    return '#216e39'
  }

  // 生成日历网格数据
  const calendarData = useMemo(() => {
    const targetMonth = month || activityData.month
    const [year, monthNum] = targetMonth.split('-').map(Number)
    
    if (!year || !monthNum) return []

    // 获取该月的第一天和最后一天
    const firstDay = new Date(year, monthNum - 1, 1)
    const lastDay = new Date(year, monthNum, 0)
    
    // 获取第一天是周几（0-6，0 为周日）
    const startDayOfWeek = firstDay.getDay()
    
    // 获取总天数
    const totalDays = lastDay.getDate()
    
    // 创建活动映射
    const activityMap = new Map(
      activityData.days.map((day) => [day.date, day])
    )
    
    // 生成网格（包括前面的空白）
    const weeks: Array<Array<{ date: string | null; day?: any }>> = []
    let currentWeek: Array<{ date: string | null; day?: any }> = []
    
    // 填充前面的空白
    for (let i = 0; i < startDayOfWeek; i++) {
      currentWeek.push({ date: null })
    }
    
    // 填充日期
    for (let day = 1; day <= totalDays; day++) {
      const dateStr = `${year}-${String(monthNum).padStart(2, '0')}-${String(day).padStart(2, '0')}`
      currentWeek.push({
        date: dateStr,
        day: activityMap.get(dateStr) || { count: 0, intensity: 0 },
      })
      
      if (currentWeek.length === 7) {
        weeks.push(currentWeek)
        currentWeek = []
      }
    }
    
    // 填充最后的空白
    while (currentWeek.length < 7 && currentWeek.length > 0) {
      currentWeek.push({ date: null })
    }
    if (currentWeek.length > 0) {
      weeks.push(currentWeek)
    }
    
    return weeks
  }, [activityData, month])

  // 星期标题
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']

  // 月份标题
  const monthTitle = month || activityData.month
  const [year, monthNum] = monthTitle.split('-')
  const monthNames = [
    '一月', '二月', '三月', '四月', '五月', '六月',
    '七月', '八月', '九月', '十月', '十一月', '十二月',
  ]
  const displayMonth = monthNum ? monthNames[parseInt(monthNum) - 1] : ''

  // 自定义 Day Cell
  const DayCell = ({ date, day }: { date: string | null; day?: any }) => {
    if (!date) {
      return <div style={{ width: 14, height: 14 }} />
    }

    const color = getColorByIntensity(day?.intensity || 0)
    const count = day?.count || 0

    return (
      <Tooltip
        title={
          count > 0
            ? `${date}：练习 ${count} 次`
            : `${date}：未练习`
        }
      >
        <div
          onClick={() => onDayClick?.(date)}
          style={{
            width: compact ? 10 : 14,
            height: compact ? 10 : 14,
            backgroundColor: color,
            borderRadius: compact ? 1 : 2,
            cursor: onDayClick ? 'pointer' : 'default',
            transition: 'transform 0.1s',
            border: '1px solid rgba(0,0,0,0.05)',
          }}
          onMouseEnter={(e) => {
            if (onDayClick) {
              e.currentTarget.style.transform = 'scale(1.2)'
            }
          }}
          onMouseLeave={(e) => {
            if (onDayClick) {
              e.currentTarget.style.transform = 'scale(1)'
            }
          }}
        />
      </Tooltip>
    )
  }

  return (
    <Card
      size={compact ? 'small' : 'default'}
      title={
        <Space>
          <CalendarOutlined />
          <span>{title || `${year}年 ${displayMonth}`}</span>
          <Text type="secondary" style={{ fontSize: 12 }}>
            共练习 {activityData.total_practice_days} 天
          </Text>
        </Space>
      }
      styles={{
        body: { padding: compact ? 12 : 16 },
      }}
      style={{ borderRadius: 8 }}
    >
      <Space direction="vertical" size="small" style={{ width: '100%' }}>
        {/* 星期标题 */}
        <div
          style={{
            display: 'flex',
            gap: compact ? 2 : 3,
            marginBottom: 4,
          }}
        >
          {weekDays.map((day) => (
            <div
              key={day}
              style={{
                width: compact ? 10 : 14,
                textAlign: 'center',
                fontSize: 9,
                color: '#999',
              }}
            >
              {day}
            </div>
          ))}
        </div>

        {/* 日历网格 */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: compact ? 2 : 3,
          }}
        >
          {calendarData.map((week, weekIndex) => (
            <div
              key={weekIndex}
              style={{
                display: 'flex',
                gap: compact ? 2 : 3,
              }}
            >
              {week.map((cell, cellIndex) => (
                <DayCell
                  key={cellIndex}
                  date={cell.date}
                  day={cell.day}
                />
              ))}
            </div>
          ))}
        </div>

        {/* 图例 */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 4,
            marginTop: 8,
          }}
        >
          <Text type="secondary" style={{ fontSize: 11 }}>
            较少
          </Text>
          {[0, 0.25, 0.5, 0.75, 1].map((intensity) => (
            <div
              key={intensity}
              style={{
                width: compact ? 8 : 10,
                height: compact ? 8 : 10,
                backgroundColor: getColorByIntensity(intensity),
                borderRadius: compact ? 1 : 2,
                border: '1px solid rgba(0,0,0,0.05)',
              }}
            />
          ))}
          <Text type="secondary" style={{ fontSize: 11 }}>
            较多
          </Text>
        </div>
      </Space>
    </Card>
  )
}

export default HeatmapCalendar
