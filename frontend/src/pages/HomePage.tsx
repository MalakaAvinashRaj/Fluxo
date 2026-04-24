import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowUp, Clock, Trash2, Bookmark, BookmarkCheck, MoreVertical,
  Zap, Database, Search, Cpu, Layers, Github, Smartphone,
} from 'lucide-react'
import { getAllProjects, deleteProject, updateProject, createProject, getProject } from '../utils/projects'
import type { Project } from '../utils/projects'
import { apiService } from '../services/api'

const API = 'http://localhost:8080'

async function pruneStaleProjects(): Promise<void> {
  const projects = getAllProjects()
  if (projects.length === 0) return
  await Promise.all(
    projects.map(async (p) => {
      if (p.pinned) return
      try {
        const res = await fetch(`${API}/sessions/${p.sessionId}`)
        if (res.status === 404) deleteProject(p.projectId)
      } catch {}
    })
  )
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function ProjectMenu({ project, onSave, onDelete }: {
  project: Project; onSave: () => void; onDelete: () => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div ref={ref} className="relative" onClick={e => e.stopPropagation()}>
      <button
        onClick={() => setOpen(o => !o)}
        className="p-1 rounded transition-colors"
        style={{ color: 'var(--text-4)' }}
        onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-2)')}
        onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-4)')}
      >
        <MoreVertical className="h-3.5 w-3.5" />
      </button>
      {open && (
        <div
          className="absolute right-0 top-7 z-50 w-40 rounded-lg shadow-2xl overflow-hidden"
          style={{ backgroundColor: 'var(--surface-raised)', border: '1px solid var(--border-strong)' }}
        >
          <button
            onClick={() => { onSave(); setOpen(false) }}
            className="flex items-center gap-2 w-full px-3 py-2 text-xs transition-colors"
            style={{ color: 'var(--text-2)' }}
            onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--surface-overlay)')}
            onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
          >
            {project.pinned
              ? <BookmarkCheck className="h-3.5 w-3.5" style={{ color: 'var(--accent)' }} />
              : <Bookmark className="h-3.5 w-3.5" />}
            {project.pinned ? 'Unsave' : 'Save'}
          </button>
          <div className="h-px" style={{ backgroundColor: 'var(--border)' }} />
          <button
            onClick={() => { onDelete(); setOpen(false) }}
            className="flex items-center gap-2 w-full px-3 py-2 text-xs text-red-400 transition-colors"
            onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--surface-overlay)')}
            onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
          >
            <Trash2 className="h-3.5 w-3.5" />
            Delete
          </button>
        </div>
      )}
    </div>
  )
}

const HOW_IT_WORKS = [
  {
    step: '01',
    Icon: Zap,
    title: 'Describe',
    desc: 'Type what you want a counter app, a weather UI, a social feed. No templates, no drag-and-drop.',
  },
  {
    step: '02',
    Icon: Search,
    title: 'Agent Plans & Retrieves',
    desc: 'A planning pass generates a targeted retrieval query. The RAG pipeline pulls the most relevant Flutter patterns from the knowledge base.',
  },
  {
    step: '03',
    Icon: Smartphone,
    title: 'Live Preview',
    desc: 'The autonomous agent writes code, builds it in Docker, and streams a live preview directly to your screen.',
  },
]

const UNDER_THE_HOOD = [
  {
    Icon: Database,
    title: 'RAG Pipeline',
    desc: 'ChromaDB vector store with semantically chunked Flutter docs. Retrieves the most relevant widget patterns and error fixes before every generation call.',
  },
  {
    Icon: Search,
    title: 'Planning Pass',
    desc: 'A dedicated LLM call before the coding loop generates a precise retrieval query — not the raw user prompt. Dramatically improves retrieval accuracy.',
  },
  {
    Icon: Cpu,
    title: 'Autonomous Agent',
    desc: 'Tool-calling loop with file operations, shell command execution, and error recovery. Builds complete Flutter apps without human steering.',
  },
  {
    Icon: Layers,
    title: 'Streaming Architecture',
    desc: 'SSE-based streaming from Python backend to React frontend. Build status, errors, and file diffs surface in real time as the agent works.',
  },
]

const STACK = ['Python', 'FastAPI', 'OpenAI', 'ChromaDB', 'React', 'Docker', 'Flutter']
const EXAMPLES = ['Counter app', 'Todo list', 'Weather UI', 'Calculator', 'Notes app']

type ServerSession = {
  session_id: string
  created_at: string
  last_active: string
  phase: string
  message_count: number
  has_build: boolean
  preview_url: string | null
}

export default function HomePage() {
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState('')
  const [isStarting, setIsStarting] = useState(false)
  const [projects, setProjects] = useState<Project[]>(getAllProjects)
  const [serverSessions, setServerSessions] = useState<ServerSession[]>([])
  const [quota, setQuota] = useState({ projects_used: 0, projects_remaining: 4, messages_limit: 20 })

  const refresh = () => setProjects(getAllProjects())

  useEffect(() => {
    pruneStaleProjects().then(refresh)
    apiService.getMySessions().then(({ sessions, quota: q }) => {
      setServerSessions(sessions)
      setQuota(q)
    })
  }, [])

  const handleContinueSession = (s: ServerSession) => {
    // If we already have this session in local storage, go straight there
    const existing = getAllProjects().find(p => p.sessionId === s.session_id)
    if (existing) {
      navigate(`/workspace/${existing.projectId}`)
      return
    }
    // Otherwise create a local project entry so WorkspacePage can restore it
    const projectId = s.session_id
    if (!getProject(projectId)) {
      createProject(projectId, s.session_id, `Project ${new Date(s.created_at).toLocaleDateString()}`)
      if (s.preview_url) {
        updateProject(projectId, { previewUrl: s.preview_url })
      }
    }
    navigate(`/workspace/${projectId}`)
  }

  const handleStart = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!prompt.trim()) return
    setIsStarting(true)
    const projectId = crypto.randomUUID()
    navigate(`/workspace/${projectId}`, { state: { prompt: prompt.trim() } })
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleStart()
    }
  }

  const handleSave = async (project: Project) => {
    const nowPinned = !project.pinned
    updateProject(project.projectId, { pinned: nowPinned })
    refresh()
    try {
      await fetch(`${API}/sessions/${project.sessionId}/pin`, { method: nowPinned ? 'POST' : 'DELETE' })
    } catch {}
  }

  const handleDelete = async (project: Project) => {
    deleteProject(project.projectId)
    refresh()
    try {
      await fetch(`${API}/sessions/${project.sessionId}/full`, { method: 'DELETE' })
    } catch {}
  }

  const pinnedProjects = projects.filter(p => p.pinned)
  const recentProjects = projects.filter(p => !p.pinned)

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: 'var(--bg)', color: 'var(--text-1)' }}
    >

      {/* ── Header ───────────────────────────────────────────────── */}
      <header
        className="px-6 py-4 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md"
        style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'rgba(20,20,20,0.85)' }}
      >
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4" style={{ color: 'var(--accent)' }} strokeWidth={2.5} />
          <span className="text-sm font-semibold tracking-tight" style={{ color: 'var(--text-1)' }}>Fluxo</span>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="https://github.com/avinashrajmalaka/fluxo"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all"
            style={{ color: 'var(--text-3)', backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
            onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-1)'; e.currentTarget.style.borderColor = 'var(--border-strong)' }}
            onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-3)'; e.currentTarget.style.borderColor = 'var(--border)' }}
          >
            <Github className="h-3.5 w-3.5" />
            GitHub
          </a>
        </div>
      </header>

      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section className="flex flex-col items-center justify-center px-6 pt-16 pb-16">

        {/* Badge */}
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-full mb-10 text-xs font-medium"
          style={{ backgroundColor: 'var(--accent-bg)', border: '1px solid var(--accent-border)', color: 'var(--accent)' }}
        >
          <div className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: 'var(--accent)' }} />
          Autonomous AI · RAG Pipeline · Live Flutter Preview
        </div>

        <h1
          className="font-semibold tracking-tight text-center mb-5 leading-tight"
          style={{ color: 'var(--text-1)', fontSize: 'clamp(2.2rem, 4.5vw, 3.8rem)' }}
        >
          Describe an app.<br />Watch it build itself.
        </h1>

        <p className="text-base text-center mb-14 max-w-md leading-relaxed" style={{ color: 'var(--text-3)' }}>
          An autonomous AI agent that plans, retrieves relevant patterns, writes Flutter code,
          and streams a live preview from a single prompt.
        </p>

        {/* Input box */}
        <div className="w-full max-w-xl">
          <form onSubmit={handleStart} className="mb-4">
            <div
              className="rounded-2xl overflow-hidden"
              style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border-strong)',
                boxShadow: '0 4px 32px rgba(0,0,0,0.12), 0 1px 4px rgba(0,0,0,0.06)',
              }}
            >
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe your Flutter app..."
                rows={3}
                className="w-full bg-transparent text-sm px-4 pt-4 pb-3 resize-none outline-none leading-relaxed"
                style={{ color: 'var(--text-1)', caretColor: 'var(--accent)' }}
                disabled={isStarting}
                autoFocus
              />
              <div className="flex items-center justify-between px-3 pb-3">
                <span className="text-xs" style={{ color: 'var(--text-4)' }}>Shift+Enter for new line</span>
                <button
                  type="submit"
                  disabled={isStarting || !prompt.trim()}
                  className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors disabled:opacity-30"
                  style={{ backgroundColor: 'var(--accent)', color: '#000' }}
                >
                  {isStarting
                    ? <div className="w-3 h-3 border-2 border-black/40 border-t-black rounded-full animate-spin" />
                    : <ArrowUp className="h-3.5 w-3.5" strokeWidth={2.5} />}
                </button>
              </div>
            </div>
          </form>

          {/* Quota indicator */}
          {quota.projects_used > 0 && (
            <p className="text-center text-xs mb-4" style={{ color: 'var(--text-4)' }}>
              <span style={{ color: quota.projects_remaining === 0 ? '#f87171' : 'var(--text-3)' }}>
                {quota.projects_used} of 4 projects used
              </span>
              {quota.projects_remaining === 0 && ' · limit reached'}
            </p>
          )}

          {/* Example chips */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {EXAMPLES.map(ex => (
              <button
                key={ex}
                onClick={() => {
                  const projectId = crypto.randomUUID()
                  navigate(`/workspace/${projectId}`, { state: { prompt: `Create a ${ex.toLowerCase()}` } })
                }}
                className="px-3 py-1.5 rounded-full text-xs transition-all duration-150"
                style={{ border: '1px solid var(--border-strong)', color: 'var(--text-3)', backgroundColor: 'transparent' }}
                onMouseEnter={e => {
                  e.currentTarget.style.backgroundColor = 'var(--surface)'
                  e.currentTarget.style.borderColor = 'var(--accent)'
                  e.currentTarget.style.color = 'var(--text-1)'
                  e.currentTarget.style.boxShadow = '0 2px 12px rgba(68,214,44,0.15)'
                  e.currentTarget.style.transform = 'translateY(-1px)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                  e.currentTarget.style.borderColor = 'var(--border-strong)'
                  e.currentTarget.style.color = 'var(--text-3)'
                  e.currentTarget.style.boxShadow = 'none'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      </section>

      <div style={{ borderTop: '1px solid var(--border)' }} />

      {/* ── How it works ─────────────────────────────────────────── */}
      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto">
          <p
            className="text-xs font-semibold uppercase tracking-widest mb-14 text-center"
            style={{ color: 'var(--accent)' }}
          >
            How it works
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {HOW_IT_WORKS.map(({ step, Icon, title, desc }) => (
              <div key={step} className="flex flex-col gap-4">
                <div className="flex items-center gap-3">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                    style={{ backgroundColor: 'var(--accent-bg)', border: '1px solid var(--accent-border)' }}
                  >
                    <Icon className="h-4 w-4" style={{ color: 'var(--accent)' }} />
                  </div>
                  <span className="text-xs font-mono font-medium" style={{ color: 'var(--text-4)' }}>{step}</span>
                </div>
                <div>
                  <p className="text-sm font-semibold mb-2" style={{ color: 'var(--text-1)' }}>{title}</p>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--text-3)' }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div style={{ borderTop: '1px solid var(--border)' }} />

      {/* ── Under the hood ───────────────────────────────────────── */}
      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto">
          <p
            className="text-xs font-semibold uppercase tracking-widest mb-3 text-center"
            style={{ color: 'var(--text-4)' }}
          >
            Under the hood
          </p>
          <h2
            className="text-2xl font-semibold tracking-tight text-center mb-14"
            style={{ color: 'var(--text-1)' }}
          >
            Built for AI engineers
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {UNDER_THE_HOOD.map(({ Icon, title, desc }) => (
              <div
                key={title}
                className="p-5 rounded-2xl transition-all duration-150"
                style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--border-strong)'
                  e.currentTarget.style.boxShadow = '0 4px 20px rgba(0,0,0,0.08)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border)'
                  e.currentTarget.style.boxShadow = 'none'
                }}
              >
                <div className="flex items-center gap-2.5 mb-3">
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
                    style={{ backgroundColor: 'var(--accent-bg)', border: '1px solid var(--accent-border)' }}
                  >
                    <Icon className="h-3.5 w-3.5" style={{ color: 'var(--accent)' }} />
                  </div>
                  <p className="text-sm font-semibold" style={{ color: 'var(--text-1)' }}>{title}</p>
                </div>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-3)' }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <div style={{ borderTop: '1px solid var(--border)' }} />

      {/* ── Tech stack ───────────────────────────────────────────── */}
      <section className="px-6 py-14 flex flex-col items-center gap-5">
        <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-4)' }}>
          Built with
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          {STACK.map(tech => (
            <span
              key={tech}
              className="px-3 py-1.5 rounded-full text-xs font-medium"
              style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-2)' }}
            >
              {tech}
            </span>
          ))}
        </div>
      </section>

      {/* ── Your previous projects (server-side, IP-based) ────────── */}
      {serverSessions.length > 0 && (
        <div className="px-6 py-10" style={{ borderTop: '1px solid var(--border)' }}>
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Clock className="h-3 w-3" style={{ color: 'var(--text-3)' }} />
                <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-3)' }}>
                  Your previous projects
                </span>
              </div>
              <span className="text-xs" style={{ color: 'var(--text-4)' }}>
                {quota.projects_used} of 4 used
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {serverSessions.map(s => (
                <button
                  key={s.session_id}
                  onClick={() => handleContinueSession(s)}
                  className="text-left rounded-xl p-3 transition-all duration-150 group"
                  style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)' }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'var(--border-strong)'
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 6px 24px rgba(0,0,0,0.12)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'var(--border)'
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                >
                  {/* Preview indicator */}
                  <div
                    className="w-full h-12 rounded-lg mb-3 flex items-center justify-center"
                    style={{ backgroundColor: 'var(--surface-raised)', border: '1px solid var(--border)' }}
                  >
                    {s.has_build
                      ? <div className="flex items-center gap-1.5">
                          <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--accent)' }} />
                          <span className="text-xs" style={{ color: 'var(--text-3)' }}>Built</span>
                        </div>
                      : <div className="w-1 h-1 rounded-full" style={{ backgroundColor: 'var(--border-strong)' }} />}
                  </div>
                  <p className="text-xs font-medium truncate mb-1" style={{ color: 'var(--text-2)' }}>
                    {new Date(s.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs" style={{ color: 'var(--text-4)' }}>
                      {timeAgo(s.last_active)}
                    </span>
                    <span className="text-xs" style={{ color: 'var(--text-4)' }}>
                      {s.message_count}/20 msgs
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Projects ─────────────────────────────────────────────── */}
      {projects.length > 0 && (
        <div className="px-6 py-10" style={{ borderTop: '1px solid var(--border)' }}>
          <div className="max-w-4xl mx-auto space-y-8">
            {pinnedProjects.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <BookmarkCheck className="h-3 w-3" style={{ color: 'var(--accent)' }} />
                  <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--accent)' }}>Saved</span>
                </div>
                <ProjectGrid
                  projects={pinnedProjects}
                  onOpen={p => navigate(`/workspace/${p.projectId}`)}
                  onSave={handleSave}
                  onDelete={handleDelete}
                />
              </section>
            )}
            {recentProjects.length > 0 && (
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Clock className="h-3 w-3" style={{ color: 'var(--text-3)' }} />
                  <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-3)' }}>Recent</span>
                </div>
                <ProjectGrid
                  projects={recentProjects}
                  onOpen={p => navigate(`/workspace/${p.projectId}`)}
                  onSave={handleSave}
                  onDelete={handleDelete}
                />
              </section>
            )}
          </div>
        </div>
      )}

    </div>
  )
}

function ProjectGrid({ projects, onOpen, onSave, onDelete }: {
  projects: Project[]
  onOpen: (p: Project) => void
  onSave: (p: Project) => void
  onDelete: (p: Project) => void
}) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2">
      {projects.map(project => (
        <div
          key={project.projectId}
          role="button"
          onClick={() => onOpen(project)}
          className="group relative rounded-xl p-3 transition-all duration-150"
          style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', boxShadow: '0 1px 4px rgba(0,0,0,0.06)', cursor: 'none' }}
          onMouseEnter={e => {
            e.currentTarget.style.boxShadow = '0 6px 24px rgba(0,0,0,0.12)'
            e.currentTarget.style.transform = 'translateY(-2px)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.boxShadow = '0 1px 4px rgba(0,0,0,0.06)'
            e.currentTarget.style.transform = 'translateY(0)'
          }}
        >
          <div
            className="w-full h-14 rounded-lg mb-3 flex items-center justify-center"
            style={{ backgroundColor: 'var(--surface-raised)', border: '1px solid var(--border)' }}
          >
            {project.previewUrl
              ? <div className="flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--accent)' }} />
                  <span className="text-xs" style={{ color: 'var(--text-3)' }}>Live</span>
                </div>
              : <div className="w-1 h-1 rounded-full" style={{ backgroundColor: 'var(--border-strong)' }} />}
          </div>
          <div className="flex items-start justify-between gap-1">
            <p className="text-xs truncate flex-1 leading-snug" style={{ color: 'var(--text-2)' }}>
              {project.name}
            </p>
            <ProjectMenu project={project} onSave={() => onSave(project)} onDelete={() => onDelete(project)} />
          </div>
          <div className="flex items-center justify-between mt-1.5">
            <span className="text-xs" style={{ color: 'var(--text-4)' }}>{timeAgo(project.createdAt)}</span>
            {project.pinned && <BookmarkCheck className="h-2.5 w-2.5" style={{ color: 'var(--accent)' }} />}
          </div>
        </div>
      ))}
    </div>
  )
}
