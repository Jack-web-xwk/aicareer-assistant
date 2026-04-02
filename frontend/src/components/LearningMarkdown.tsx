import type { ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Typography } from 'antd'

const { Title, Paragraph, Text } = Typography

const baseComponents = {
  a: ({ href, children }: { href?: string; children?: ReactNode }) => {
    const external = Boolean(href?.startsWith('http'))
    return (
      <a
        href={href}
        target={external ? '_blank' : undefined}
        rel={external ? 'noreferrer noopener' : undefined}
        style={{ color: 'var(--color-info)' }}
      >
        {children}
      </a>
    )
  },
  h1: ({ children }: { children?: ReactNode }) => (
    <Title level={3} style={{ color: 'var(--color-text-primary)', marginTop: 16 }}>
      {children}
    </Title>
  ),
  h2: ({ children }: { children?: ReactNode }) => (
    <Title level={4} style={{ color: 'var(--color-text-primary)', marginTop: 12 }}>
      {children}
    </Title>
  ),
  h3: ({ children }: { children?: ReactNode }) => (
    <Title level={5} style={{ color: 'var(--color-text-primary)', marginTop: 8 }}>
      {children}
    </Title>
  ),
  p: ({ children }: { children?: ReactNode }) => (
    <Paragraph style={{ color: 'var(--color-text-secondary)' }}>{children}</Paragraph>
  ),
  li: ({ children }: { children?: ReactNode }) => (
    <li style={{ color: 'var(--color-text-secondary)' }}>{children}</li>
  ),
  strong: ({ children }: { children?: ReactNode }) => (
    <Text strong style={{ color: 'var(--color-text-primary)' }}>
      {children}
    </Text>
  ),
  blockquote: ({ children }: { children?: ReactNode }) => (
    <blockquote
      style={{
        borderLeft: '4px solid var(--color-primary)',
        margin: '12px 0',
        paddingLeft: 16,
        color: 'var(--color-text-secondary)',
        background: 'var(--color-bg-tertiary)',
        borderRadius: '0 8px 8px 0',
      }}
    >
      {children}
    </blockquote>
  ),
  table: ({ children }: { children?: ReactNode }) => (
    <div style={{ overflowX: 'auto', margin: '12px 0' }}>
      <table
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          fontSize: 14,
          border: '1px solid var(--color-border)',
          borderRadius: 8,
        }}
      >
        {children}
      </table>
    </div>
  ),
  thead: ({ children }: { children?: ReactNode }) => <thead style={{ background: 'var(--color-bg-tertiary)' }}>{children}</thead>,
  th: ({ children }: { children?: ReactNode }) => (
    <th
      style={{
        border: '1px solid var(--color-border)',
        padding: '8px 12px',
        textAlign: 'left',
        color: 'var(--color-text-primary)',
      }}
    >
      {children}
    </th>
  ),
  td: ({ children }: { children?: ReactNode }) => (
    <td
      style={{
        border: '1px solid var(--color-border)',
        padding: '8px 12px',
        color: 'var(--color-text-secondary)',
      }}
    >
      {children}
    </td>
  ),
  pre: ({ children }: { children?: ReactNode }) => (
    <pre
      style={{
        background: 'var(--color-bg-tertiary)',
        padding: 12,
        borderRadius: 8,
        overflowX: 'auto',
        fontSize: 13,
        border: '1px solid var(--color-border)',
        margin: '12px 0',
      }}
    >
      {children}
    </pre>
  ),
  code: ({ className, children }: { className?: string; children?: ReactNode }) => {
    const isFenced = Boolean(className?.startsWith('language-'))
    if (isFenced) {
      return <code className={className}>{children}</code>
    }
    return (
      <code
        style={{
          background: 'var(--color-bg-tertiary)',
          padding: '2px 6px',
          borderRadius: 4,
          fontSize: '0.9em',
          color: 'var(--color-primary-dark)',
        }}
      >
        {children}
      </code>
    )
  },
}

export interface LearningMarkdownProps {
  content: string
  className?: string
  /** GitHub Flavored Markdown（表格、任务列表等），AI 前沿日报内容建议开启 */
  gfm?: boolean
}

export function LearningMarkdown({ content, className, gfm = false }: LearningMarkdownProps) {
  return (
    <div className={className}>
      <ReactMarkdown remarkPlugins={gfm ? [remarkGfm] : []} components={baseComponents}>
        {content || '_暂无内容_'}
      </ReactMarkdown>
    </div>
  )
}
