import React, { useState, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// ---------------------------------------------------------------------------
// Sample salary slip (matches Python SAMPLE_SALARY_SLIP_MARKDOWN)
// ---------------------------------------------------------------------------
const SAMPLE_SLIP = `# Salary Slip — March 2026

**Company:** Digital Transformation Corp
**Employee Name:** Aarav Mehta
**Employee ID:** EMP1001
**Designation:** Operations Analyst
**Pay Period:** March 2026
**Pay Date:** 2026-03-31

## Earnings

| Component            | Amount (AED) |
|----------------------|-------------|
| Basic Salary         | 6,000.00    |
| Housing Allowance    | 1,157.86    |
| Transport Allowance  | 550.00      |
| Food Allowance       | 150.00      |
| Mobile Allowance     | 100.00      |
| Special Allowance    | 150.00      |
| Overtime             | 250.00      |
| **Gross Earnings**   | **8,357.86**|

## Deductions

| Component            | Amount (AED) |
|----------------------|-------------|
| Total Deductions     | 0.00        |

## Net Salary: AED 8,357.86`

// ---------------------------------------------------------------------------
// Agent pipeline configuration
// ---------------------------------------------------------------------------
const AGENTS_CONFIG = [
  {
    id: 1,
    name: 'Document Verification Agent',
    icon: '🔍',
    desc: 'Validates structure, maths & fraud signals',
  },
  {
    id: 2,
    name: 'Salary Analysis Agent',
    icon: '📊',
    desc: 'Code interpreter · CSV history · variation thresholds',
  },
  {
    id: 3,
    name: 'Document Summary Agent',
    icon: '📝',
    desc: 'Synthesises both results into a Markdown report',
  },
  {
    id: 4,
    name: 'Word Executor',
    icon: '💾',
    desc: 'Saves Markdown + Word (.docx) documents',
  },
]

const INITIAL_AGENTS = AGENTS_CONFIG.map(a => ({
  ...a,
  taskStatus: 'idle',   // idle | running | complete | error
  output: '',
}))

// ---------------------------------------------------------------------------
// Spinner component
// ---------------------------------------------------------------------------
function Spinner({ size = 18 }) {
  return (
    <svg
      className="spinner-svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        cx="12" cy="12" r="9"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeDasharray="42 14"
      />
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Status icon alongside an agent card
// ---------------------------------------------------------------------------
function StatusIcon({ status }) {
  if (status === 'running') return <Spinner size={20} />
  if (status === 'complete') return <span className="icon-tick">✓</span>
  if (status === 'error')    return <span className="icon-error">✗</span>
  return <span className="icon-idle">○</span>
}

// ---------------------------------------------------------------------------
// Single agent card
// ---------------------------------------------------------------------------
function AgentCard({ agent, isLast }) {
  const { taskStatus, output } = agent
  const [expanded, setExpanded] = useState(false)

  // Auto-expand when output arrives
  React.useEffect(() => {
    if (output) setExpanded(true)
  }, [output])

  return (
    <div className="agent-row">
      <div className={`agent-card agent-${taskStatus}`}>
        <div className="agent-card-header" onClick={() => output && setExpanded(e => !e)}>
          <div className="agent-number">{agent.id}</div>
          <div className="agent-meta">
            <div className="agent-name">{agent.icon} {agent.name}</div>
            <div className="agent-desc">{agent.desc}</div>
          </div>
          <div className="agent-status-area">
            <StatusIcon status={taskStatus} />
            {output && (
              <span className="agent-toggle">{expanded ? '▲' : '▼'}</span>
            )}
          </div>
        </div>

        {expanded && output && (
          <div className="agent-output">
            <pre>{output.length > 800 ? output.slice(0, 800) + '\n\n… [truncated — full result in report]' : output}</pre>
          </div>
        )}
      </div>

      {!isLast && (
        <div className={`pipeline-connector ${taskStatus === 'complete' ? 'connector-lit' : ''}`}>
          <div className="connector-line" />
          <div className="connector-arrow">▼</div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Workflow status banner
// ---------------------------------------------------------------------------
function StatusBanner({ status, error }) {
  if (status === 'idle') return null
  if (status === 'complete') {
    return (
      <div className="banner banner-complete">
        <span className="banner-tick">✓</span>
        <span>Workflow complete — all agents finished successfully</span>
      </div>
    )
  }
  if (status === 'error') {
    return (
      <div className="banner banner-error">
        <span>⚠ Error: {error}</span>
      </div>
    )
  }
  return (
    <div className="banner banner-running">
      <Spinner size={16} />
      <span>Workflow running…</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------
export default function App() {
  const [slip, setSlip] = useState(SAMPLE_SLIP)
  const [status, setStatus] = useState('idle')     // idle | running | complete | error
  const [agents, setAgents] = useState(INITIAL_AGENTS)
  const [markdown, setMarkdown] = useState('')
  const [wordPath, setWordPath] = useState(null)
  const [error, setError] = useState('')
  const reportRef = useRef(null)
  const readerRef = useRef(null)

  const updateAgent = (id, taskStatus, output) => {
    setAgents(prev =>
      prev.map(a =>
        a.id === id ? { ...a, taskStatus, output: output !== undefined ? output : a.output } : a,
      ),
    )
  }

  const reset = () => {
    if (readerRef.current) {
      try { readerRef.current.cancel() } catch {}
      readerRef.current = null
    }
    setStatus('idle')
    setAgents(INITIAL_AGENTS)
    setMarkdown('')
    setWordPath(null)
    setError('')
  }

  const run = async () => {
    reset()
    // Small delay so reset() state settles
    await new Promise(r => setTimeout(r, 50))

    setStatus('running')
    setAgents(AGENTS_CONFIG.map(a => ({ ...a, taskStatus: 'idle', output: '' })))

    try {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ salary_slip: slip }),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Server returned ${res.status}: ${text}`)
      }

      const reader = res.body.getReader()
      readerRef.current = reader
      const dec = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += dec.decode(value, { stream: true })

        // SSE lines are separated by \n\n; parse line-by-line
        const lines = buf.split('\n')
        buf = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          let ev
          try { ev = JSON.parse(line.slice(6)) }
          catch { continue }

          switch (ev.event) {
            case 'agent_start':
              updateAgent(ev.agent, 'running')
              break
            case 'agent_complete':
              updateAgent(ev.agent, 'complete', ev.output ?? '')
              break
            case 'executor_start':
              updateAgent(4, 'running')
              break
            case 'executor_complete':
              updateAgent(4, 'complete',
                ev.word_doc_path
                  ? '✓ Markdown report saved\n✓ Word document saved'
                  : '✓ Markdown report saved\n(Word: python-docx not available)',
              )
              setMarkdown(ev.markdown ?? '')
              setWordPath(ev.word_doc_path || null)
              // Scroll to report panel
              setTimeout(() => reportRef.current?.scrollIntoView({ behavior: 'smooth' }), 300)
              break
            case 'done':
              setStatus('complete')
              break
            case 'error':
              setError(ev.message ?? 'Unknown error')
              setStatus('error')
              break
          }
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') {
        setError(e.message)
        setStatus('error')
      }
    }
  }

  const downloadWord = () => window.open('/api/download', '_blank')

  const isRunning = status === 'running'
  const isDone    = status === 'complete'

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-inner">
          <div className="header-brand">
            <div className="header-logo">⚡</div>
            <div>
              <div className="header-title">Payslip Verification Workflow</div>
              <div className="header-sub">Azure AI Agent Service · Three-agent pipeline + Word executor</div>
            </div>
          </div>
          <StatusBanner status={status} error={error} />
        </div>
      </header>

      {/* ── Body ── */}
      <div className="body-grid">

        {/* ── Left column ── */}
        <div className="col-left">

          {/* Input card */}
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">📄 Salary Slip Input</h2>
            </div>
            <textarea
              className="slip-textarea"
              value={slip}
              onChange={e => setSlip(e.target.value)}
              disabled={isRunning}
              placeholder="Paste salary slip content (Markdown or JSON)…"
              spellCheck={false}
            />
            <div className="input-footer">
              <button
                className="btn-run"
                onClick={run}
                disabled={isRunning}
              >
                {isRunning
                  ? <><Spinner size={15} /> Running…</>
                  : isDone
                    ? '↻ Run Again'
                    : '▶ Run Workflow'}
              </button>
              {status !== 'idle' && (
                <button className="btn-secondary" onClick={reset} disabled={isRunning}>
                  ✕ Reset
                </button>
              )}
            </div>
          </section>

          {/* Pipeline card */}
          <section className="card">
            <div className="card-header">
              <h2 className="card-title">🤖 Agent Pipeline</h2>
              {isDone && <span className="all-done-badge">✓ All complete</span>}
            </div>
            <div className="pipeline">
              {agents.map((agent, idx) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  isLast={idx === agents.length - 1}
                />
              ))}
            </div>
          </section>

        </div>

        {/* ── Right column — Report ── */}
        <div className="col-right">
          <section className="card report-card" ref={reportRef}>
            <div className="card-header">
              <h2 className="card-title">📋 Verification Report</h2>
              {markdown && (
                <button className="btn-download" onClick={downloadWord}>
                  ↓ Download Word
                </button>
              )}
            </div>

            {!markdown && (
              <div className="report-empty">
                {isRunning
                  ? <><Spinner size={28} /><p>Generating report…</p></>
                  : <><span className="report-empty-icon">📋</span><p>Run the workflow to see the report here.</p></>
                }
              </div>
            )}

            {markdown && (
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {markdown}
                </ReactMarkdown>
              </div>
            )}

            {markdown && wordPath && (
              <div className="report-footer">
                <button className="btn-download-full" onClick={downloadWord}>
                  ↓ Download Word Document
                </button>
                <span className="word-path">{wordPath.split(/[/\\]/).pop()}</span>
              </div>
            )}
          </section>
        </div>

      </div>
    </div>
  )
}
