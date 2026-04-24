import { useState, useEffect, useRef } from "react"
import { useLocation, useParams } from "react-router-dom"
import { WorkspaceHeader } from "../components/workspace/WorkspaceHeader"
import { FileExplorer } from "../components/workspace/FileExplorer"
import { CodeEditor } from "../components/workspace/CodeEditor"
import { PhonePreview } from "../components/workspace/PhonePreview"
import { ChatPanel } from "../components/workspace/ChatPanel"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { apiService, ApiError } from "../services/api"
import { useApi } from "../hooks/useApi"
import { ENV } from "../config/environment"
import { Logger } from "../utils/logger"
import { getProject, createProject, updateProject } from "../utils/projects"

type FileType = {
  path: string
  content: string
}

export type ChatMessage = {
  id: string
  role: "user" | "assistant" | "plan"
  content: string
  timestamp: Date
  planData?: { summary: string; questions: string[] }
}

function stripCodeFences(text: string): string {
  return text.replace(/```[\w]*\n[\s\S]*?```/g, '').trim()
}

export default function WorkspacePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const location = useLocation()
  const initialPrompt: string | null = location.state?.prompt ?? null

  const isNewProject = !getProject(projectId!)

  const [sessionId, setSessionId] = useState<string | null>(null)
  const [chatOpen, setChatOpen] = useState(true)
  const [activeView, setActiveView] = useState<"code" | "preview">("code")
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [files, setFiles] = useState<FileType[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  // Only show the full loading screen for brand-new projects
  const [isFirstConnect, setIsFirstConnect] = useState(isNewProject)
  const [warmupMessage, setWarmupMessage] = useState<string>('')
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'failed' | 'retrying' | 'warming_up'>(
    isNewProject ? 'connecting' : 'connected'
  )

  const logger = new Logger('WorkspacePage')
  const warmupFiredRef = useRef(false)

  const { loading: sessionLoading, error: sessionError, execute: createSession } = useApi(
    (userId: string) => apiService.createSession(userId)
  )

  // ─── Restore existing project ────────────────────────────────────────────────
  useEffect(() => {
    if (!projectId) return

    const project = getProject(projectId)

    if (project) {
      // Existing project — connect to existing session, restore state
      logger.info('Restoring existing project:', projectId, 'session:', project.sessionId)
      setSessionId(project.sessionId)
      if (project.previewUrl) setPreviewUrl(project.previewUrl)
      if (project.files && project.files.length > 0) {
        setFiles(project.files)
        setSelectedFile(project.files[0].path)
      }
      setConnectionStatus('connected')
      setIsFirstConnect(false)

      // Restore chat history from backend
      apiService.getSession(project.sessionId)
        .then((data: any) => {
          const history: ChatMessage[] = (data.messages ?? []).map((m: any) => ({
            id: crypto.randomUUID(),
            role: m.role as 'user' | 'assistant',
            content: m.role === 'assistant' ? stripCodeFences(m.content) : m.content,
            timestamp: new Date(),
          }))
          if (history.length > 0) setMessages(history)
          else setMessages([{ id: 'welcome', role: 'assistant', content: "Hi! What would you like to change?", timestamp: new Date() }])
        })
        .catch(() => {
          setMessages([{ id: 'welcome', role: 'assistant', content: "Hi! What would you like to change?", timestamp: new Date() }])
        })
    } else {
      // New project — go through full connect + warmup flow
      connectAndWarmup()
    }
  }, [projectId])

  // ─── New project: connect backend + warmup ───────────────────────────────────
  const connectAndWarmup = async () => {
    let retryCount = 0
    const maxRetries = 30
    let connected = false

    while (!connected && retryCount < maxRetries) {
      setConnectionStatus('connecting')
      connected = await initializeSession()
      if (!connected) {
        retryCount++
        setConnectionStatus('retrying')
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }

    if (!connected) {
      setConnectionStatus('failed')
      return
    }

    const currentSessionId = sessionStorage.getItem('__tmp_session')
    if (!currentSessionId) return

    setConnectionStatus('warming_up')
    setWarmupMessage('Starting Flutter container...')

    apiService.warmupSession(currentSessionId, (event) => {
      setWarmupMessage(event.message)

      if (event.phase === 'container_ready') {
        if (event.previewUrl) setPreviewUrl(event.previewUrl)
        setConnectionStatus('connected')
        setIsFirstConnect(false)

        // Save project to registry now that we have sessionId
        if (projectId && initialPrompt && !warmupFiredRef.current) {
          warmupFiredRef.current = true
          createProject(projectId, currentSessionId, initialPrompt.slice(0, 60))

          setMessages([{ id: 'user-init', role: 'user', content: initialPrompt, timestamp: new Date() }])
          sendMessage(initialPrompt, currentSessionId)
        }
      } else if (event.phase === 'error') {
        logger.error('Warmup error:', event.message)
        setConnectionStatus('connected')
        setIsFirstConnect(false)
      }
    }).catch(err => logger.error('Warmup failed:', err))
  }

  const initializeSession = async (): Promise<boolean> => {
    try {
      const health = await apiService.healthCheck()
      if (health.status !== 'healthy') return false

      const session = await createSession('workspace_user')
      if (session) {
        sessionStorage.setItem('__tmp_session', session.session_id)
        setSessionId(session.session_id)
        return true
      }
      return false
    } catch {
      return false
    }
  }

  // ─── Send message + stream response ─────────────────────────────────────────
  const sendMessage = async (prompt: string, sid?: string): Promise<void> => {
    const activeSessionId = sid || sessionId
    if (!activeSessionId) return

    setIsGenerating(true)

    const assistantMsgId = crypto.randomUUID()
    setMessages(prev => [...prev, {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }])

    try {
      let proseAccum = ''
      const statusLines: string[] = []
      let planReceived = false

      const updateMsg = (content: string) =>
        setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content } : m))

      await apiService.sendMessageStream(activeSessionId, prompt, (chunk) => {
        if (chunk.type === 'plan') {
          // Replace the placeholder assistant message with a plan card
          planReceived = true
          setMessages(prev => prev.map(m =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  role: 'plan' as const,
                  content: chunk.data?.summary ?? '',
                  planData: {
                    summary: chunk.data?.summary ?? '',
                    questions: chunk.data?.questions ?? [],
                  },
                }
              : m
          ))
        } else if (chunk.type === 'content') {
          proseAccum += chunk.data
        } else if (chunk.type === 'status') {
          const msg: string = chunk.data?.message ?? ''
          if (msg) {
            statusLines.push(msg)
            updateMsg(statusLines.join('\n'))
          }
        } else if (chunk.type === 'build_error') {
          const detail: string = chunk.data?.detail ?? ''
          statusLines.push(`❌ Build failed${detail ? ':\n' + detail : ''}`)
          updateMsg(statusLines.join('\n'))
        } else if (chunk.type === 'files') {
          const incoming: FileType[] = chunk.data ?? []
          setFiles(incoming)
          if (incoming.length > 0) setSelectedFile(incoming[0].path)
          if (projectId) updateProject(projectId, { files: incoming })
        } else if (chunk.type === 'flutter_preview' || chunk.type === 'flutter_preview_update') {
          if (chunk.data?.success && chunk.data?.previewUrl) {
            setPreviewUrl(chunk.data.previewUrl)
            if (projectId) updateProject(projectId, { previewUrl: chunk.data.previewUrl })
            setActiveView('preview')
          }
        }
      })

      // Plan event handled above — don't overwrite with prose
      if (!planReceived) {
        const finalProse = stripCodeFences(proseAccum).trim()
        const hasBuildError = statusLines.some(l => l.startsWith('❌'))
        if (finalProse && !hasBuildError) {
          updateMsg(finalProse)
        } else if (statusLines.length === 0) {
          updateMsg('Done.')
        }
      }
    } catch (error) {
      logger.error('Failed to send message:', error)
      setMessages(prev => prev.map(m =>
        m.id === assistantMsgId ? { ...m, content: 'Something went wrong. Please try again.' } : m
      ))
    } finally {
      setIsGenerating(false)
    }
  }

  // ─── Rebuild (re-runs flutter build web with existing container files) ────────
  const rebuildApp = async () => {
    const activeSessionId = sessionId
    if (!activeSessionId || isGenerating) return

    setIsGenerating(true)
    const msgId = crypto.randomUUID()
    setMessages(prev => [...prev,
      { id: crypto.randomUUID(), role: 'user', content: '🔄 Rebuild requested', timestamp: new Date() },
      { id: msgId, role: 'assistant', content: '🔨 Rebuilding Flutter app...', timestamp: new Date() },
    ])

    try {
      const res = await fetch(`${ENV.API_BASE_URL}/sessions/${activeSessionId}/rebuild`, { method: 'POST' })
      const result = await res.json()
      if (result.success) {
        setPreviewUrl(result.previewUrl)
        if (projectId) updateProject(projectId, { previewUrl: result.previewUrl })
        setActiveView('preview')
        setMessages(prev => prev.map(m => m.id === msgId ? { ...m, content: '✅ Rebuild complete! Preview updated.' } : m))
      } else {
        // result.output has compiler errors, result.error is a short msg, result.detail is FastAPI 404 format
        const detail = result.output
          ? result.output.split('\n').filter((l: string) => l.includes('Error:')).slice(0, 6).join('\n')
          : result.error ?? result.detail ?? 'Unknown error'
        setMessages(prev => prev.map(m => m.id === msgId ? { ...m, content: `❌ Rebuild failed: ${detail}` } : m))
      }
    } catch {
      setMessages(prev => prev.map(m => m.id === msgId ? { ...m, content: '❌ Rebuild request failed.' } : m))
    } finally {
      setIsGenerating(false)
    }
  }

  // Called by ChatPanel when user submits a message
  // displayText is what shows in the chat bubble (e.g. short label for fix prompts)
  const handleSendMessage = (text: string, displayText?: string) => {
    setActiveView('code') // Switch to code view so user sees files populating
    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      role: 'user',
      content: displayText ?? text,
      timestamp: new Date(),
    }])
    sendMessage(text)
  }

  // ─── Derived state ────────────────────────────────────────────────────────────
  const isLoading = isFirstConnect && (
    connectionStatus === 'connecting' ||
    connectionStatus === 'retrying' ||
    sessionLoading
  )

  const getStatusMessage = () => {
    switch (connectionStatus) {
      case 'connecting': return 'Connecting to AI Agent...'
      case 'retrying': return 'Retrying connection...'
      case 'warming_up': return warmupMessage || 'Warming up container...'
      case 'connected': return 'Connected'
      case 'failed': return 'Connection failed'
      default: return 'Initializing...'
    }
  }

  const isLoadingOrWarmingUp = isLoading || (isFirstConnect && connectionStatus === 'warming_up')
  const isFailed = connectionStatus === 'failed'

  // ─── Main workspace ───────────────────────────────────────────────────────────
  return (
    <div className="relative h-screen overflow-hidden flex flex-col" style={{ backgroundColor: 'var(--bg)', color: 'var(--text-1)' }}>
      {/* Header always visible */}
      <WorkspaceHeader
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* Status banner */}
      {(isLoadingOrWarmingUp || isFailed) && (
        <div
          className="flex items-center justify-center gap-2 px-4 py-1.5 text-xs"
          style={isFailed
            ? { backgroundColor: 'rgba(239,68,68,0.06)', borderBottom: '1px solid rgba(239,68,68,0.12)', color: '#f87171' }
            : { backgroundColor: 'var(--accent-bg)', borderBottom: '1px solid var(--accent-border)', color: 'var(--accent)' }}
        >
          {!isFailed && <div className="w-1.5 h-1.5 rounded-full bg-[#44D62C]/60 animate-pulse" />}
          <span className="text-xs">{isFailed ? 'Connection failed — make sure the backend is running' : getStatusMessage()}</span>
          {isFailed && (
            <button onClick={() => window.location.reload()} className="ml-1 underline underline-offset-2 hover:text-red-400 transition-colors">
              Retry
            </button>
          )}
        </div>
      )}

      <div className="flex flex-1 min-h-0 relative">
        {/* Chat Panel */}
        <div className={`${chatOpen ? "w-[28%]" : "w-0"} transition-all duration-300 ease-out overflow-visible relative shrink-0`} style={{ backgroundColor: 'var(--surface)', borderRight: '1px solid var(--border)', boxShadow: '2px 0 12px rgba(0,0,0,0.06)' }}>
          <div className={`h-full transition-all duration-200 ease-in-out ${chatOpen ? 'opacity-100 translate-x-0 pointer-events-auto' : 'opacity-0 -translate-x-4 pointer-events-none'}`}>
            <ChatPanel
              sessionId={sessionId}
              isGenerating={isGenerating}
              messages={messages}
              onSendMessage={handleSendMessage}
              files={files}
            />
          </div>
          {chatOpen && (
            <button
              onClick={() => setChatOpen(false)}
              className="absolute top-1/2 right-0 -translate-y-1/2 translate-x-1/2 z-20 w-5 h-10 rounded-full flex items-center justify-center transition-colors"
            style={{ backgroundColor: 'var(--surface-raised)', border: '1px solid var(--border-strong)', color: 'var(--text-3)' }}
            >
              <ChevronLeft className="h-3 w-3" />
            </button>
          )}
        </div>

        {!chatOpen && (
          <button
            onClick={() => setChatOpen(true)}
            className="absolute top-1/2 left-0 -translate-y-1/2 translate-x-1/2 z-20 w-5 h-10 rounded-full flex items-center justify-center transition-colors"
            style={{ backgroundColor: 'var(--surface-raised)', border: '1px solid var(--border-strong)', color: 'var(--text-3)' }}
          >
            <ChevronRight className="h-3 w-3" />
          </button>
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <div className="flex-1 relative min-h-0 min-w-0">
            {activeView === "code" ? (
              <div className="flex h-full min-h-0 min-w-0">
                <FileExplorer files={files} selectedFile={selectedFile} onSelectFile={setSelectedFile} />
                <CodeEditor files={files} selectedFile={selectedFile} onSelectFile={setSelectedFile} />
              </div>
            ) : (
              <PhonePreview sessionId={sessionId} previewUrl={previewUrl} isLoading={isGenerating} onRebuild={rebuildApp} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
