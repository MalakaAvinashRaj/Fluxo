import { useState, useEffect, useRef } from "react"
import { Wrench, ArrowUp, Zap } from "lucide-react"
import type { ChatMessage } from "../../pages/WorkspacePage"

type FileType = { path: string; content: string }
type ChatPanelProps = {
  sessionId: string | null
  isGenerating: boolean
  messages: ChatMessage[]
  files: FileType[]
  onSendMessage: (message: string, displayText?: string) => void
}

function isErrorMessage(content: string) { return content.split('\n').some(l => l.startsWith('❌')) }

function getRelevantFiles(err: string, files: FileType[]) {
  const hit = files.filter(f => err.includes(f.path))
  return hit.length > 0 ? hit : files
}

function buildFixPrompt(errorContent: string, files: FileType[]) {
  const relevant = getRelevantFiles(errorContent, files)
  const code = relevant.map(f => `// ${f.path}\n${f.content}`).join('\n\n')
  const errorText = errorContent.replace(/^❌\s*/, '')
  return `I got the following build error:\n\n${errorText}\n\nRelevant file(s):\n\`\`\`dart\n${code}\n\`\`\`\n\nPlease fix the error.`
}

// Group consecutive messages by role so we can style runs together
function groupMessages(messages: ChatMessage[]) {
  const groups: { role: string; messages: ChatMessage[] }[] = []
  for (const msg of messages) {
    const last = groups[groups.length - 1]
    if (last && last.role === msg.role) {
      last.messages.push(msg)
    } else {
      groups.push({ role: msg.role, messages: [msg] })
    }
  }
  return groups
}

export function ChatPanel({ sessionId, isGenerating, messages, files, onSendMessage }: ChatPanelProps) {
  const [newMessage, setNewMessage] = useState("")
  const [focused, setFocused] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isGenerating])

  useEffect(() => {
    if (!isGenerating) { setElapsed(0); return }
    setElapsed(0)
    const id = setInterval(() => setElapsed(s => s + 1), 1000)
    return () => clearInterval(id)
  }, [isGenerating])

  const fmtElapsed = (s: number) =>
    s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || isGenerating || !sessionId) return
    onSendMessage(newMessage.trim())
    setNewMessage("")
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  const handleFixWithAI = (errorContent: string) => {
    onSendMessage(buildFixPrompt(errorContent, files), '🔧 Fix build error')
  }

  const groups = groupMessages(messages)

  return (
    <div className="h-full flex flex-col relative" style={{ backgroundColor: 'var(--surface)' }}>

      {/* Slim status strip — only visible when generating */}
      <div
        className="flex items-center gap-2 px-4 overflow-hidden shrink-0 transition-all duration-300"
        style={{
          height: isGenerating ? '36px' : '0px',
          borderBottom: isGenerating ? '1px solid var(--border)' : 'none',
          opacity: isGenerating ? 1 : 0,
        }}
      >
        <Zap className="h-3 w-3 shrink-0" style={{ color: 'var(--accent)' }} />
        <span className="text-xs font-medium" style={{ color: 'var(--text-3)' }}>Thinking...</span>
        <div className="flex items-center gap-0.5 ml-1">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="w-1 h-1 rounded-full animate-bounce"
              style={{ backgroundColor: 'var(--accent)', opacity: 0.6, animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
        <span
          className="ml-auto text-xs font-mono tabular-nums"
          style={{ color: 'var(--text-4)' }}
        >
          {fmtElapsed(elapsed)}
        </span>
      </div>

      {/* Messages — flex-1 so it sits below the Thinking bar; input floats absolute over bottom */}
      <div className="flex-1 overflow-auto py-6 space-y-5" style={{ paddingLeft: '20px', paddingRight: '20px', paddingBottom: '110px', maskImage: 'linear-gradient(to bottom, transparent 0%, black 6%, black 88%, transparent 100%)', WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 6%, black 88%, transparent 100%)' }}>

        {messages.length === 0 && !isGenerating && (
          <div className="flex flex-col items-center justify-center h-full gap-3 pb-16">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ backgroundColor: 'var(--accent-bg)', border: '1px solid var(--accent-border)' }}
            >
              <Zap className="h-4 w-4" style={{ color: 'var(--accent)' }} />
            </div>
            <p className="text-xs text-center" style={{ color: 'var(--text-4)' }}>
              Start chatting to build your app
            </p>
          </div>
        )}

        {groups.map((group, gi) => (
          <div
            key={gi}
            className={`flex flex-col gap-1 ${group.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            {group.messages.map((message, mi) => (
              <div
                key={message.id}
                className={`flex flex-col gap-2 w-full ${group.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                {group.role === 'user' ? (
                  /* User bubble — soft filled pill, no border */
                  <div
                    className="max-w-[82%] px-3.5 py-2.5"
                    style={{
                      backgroundColor: 'var(--surface-overlay)',
                      borderRadius: mi === 0
                        ? '18px 18px 4px 18px'
                        : mi === group.messages.length - 1
                          ? '4px 18px 18px 18px'
                          : '4px 18px 18px 4px',
                    }}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--text-1)' }}>
                      {message.content}
                    </p>
                  </div>
                ) : (
                  /* AI response — just text, no container */
                  <div className="max-w-[96%] flex flex-col gap-2.5">
                    {isErrorMessage(message.content) ? (
                      <div className="flex flex-col gap-2">
                        {/* Show only the clean status lines — hide raw compiler errors */}
                        {message.content.split('\n')
                          .filter(l => !l.startsWith('❌') && !l.startsWith('Error:') && l.trim())
                          .map((line, i) => (
                            <p key={i} className="text-sm leading-relaxed" style={{ color: 'var(--text-2)' }}>{line}</p>
                          ))}
                        {/* Friendly error notice */}
                        <div
                          className="flex items-center gap-2 px-3 py-2 rounded-xl mt-1"
                          style={{ backgroundColor: 'rgba(239,68,68,0.05)', borderLeft: '2px solid rgba(239,68,68,0.3)' }}
                        >
                          <span className="text-sm" style={{ color: '#f87171' }}>Build ran into some errors.</span>
                        </div>
                      </div>
                    ) : (
                      <p
                        className="text-sm leading-relaxed whitespace-pre-wrap"
                        style={{ color: 'var(--text-2)' }}
                      >
                        {message.content || (
                          isGenerating && mi === group.messages.length - 1
                            ? <span className="flex items-center gap-1 h-5">
                                {[0, 1, 2].map(d => (
                                  <span
                                    key={d}
                                    className="inline-block w-1 h-1 rounded-full animate-bounce"
                                    style={{ backgroundColor: 'var(--text-4)', animationDelay: `${d * 0.15}s` }}
                                  />
                                ))}
                              </span>
                            : null
                        )}
                      </p>
                    )}

                    {isErrorMessage(message.content) && !isGenerating && (
                      <button
                        onClick={() => handleFixWithAI(message.content)}
                        className="self-start flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all"
                        style={{
                          backgroundColor: 'var(--accent-bg)',
                          border: '1px solid var(--accent-border)',
                          color: 'var(--accent)',
                        }}
                      >
                        <Wrench className="h-3 w-3" />
                        Fix with AI
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input — floating pill */}
      <div className="absolute bottom-0 left-0 right-0 px-4 pb-4 pt-2 shrink-0">
        <form onSubmit={handleSubmit}>
          <div
            className="rounded-2xl transition-all duration-150 overflow-hidden"
            style={{
              backgroundColor: 'var(--surface-raised)',
              border: `1px solid ${focused ? 'var(--border-strong)' : 'var(--border)'}`,
              boxShadow: focused ? '0 4px 20px rgba(0,0,0,0.1), 0 0 0 1px var(--accent-border)' : '0 2px 8px rgba(0,0,0,0.06)',
            }}
          >
            <textarea
              value={newMessage}
              onChange={e => setNewMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder={sessionId ? "Ask for changes..." : "Connecting..."}
              rows={1}
              className="w-full bg-transparent text-sm px-4 pt-3 pb-1 resize-none outline-none leading-relaxed"
              style={{
                color: 'var(--text-1)',
                caretColor: 'var(--accent)',
                minHeight: '44px',
                maxHeight: '120px',
              }}
              disabled={isGenerating || !sessionId}
              onInput={e => {
                const t = e.currentTarget
                t.style.height = 'auto'
                t.style.height = Math.min(t.scrollHeight, 120) + 'px'
              }}
            />
            <div className="flex items-center justify-between px-3 pb-2.5">
              <span className="text-xs" style={{ color: 'var(--text-4)' }}>↵ send &nbsp;·&nbsp; ⇧↵ newline</span>
              <button
                type="submit"
                disabled={isGenerating || !newMessage.trim() || !sessionId}
                className="w-6 h-6 rounded-lg flex items-center justify-center transition-all disabled:opacity-25"
                style={{ backgroundColor: newMessage.trim() ? 'var(--accent)' : 'var(--surface-overlay)', color: newMessage.trim() ? '#000' : 'var(--text-4)' }}
              >
                {isGenerating
                  ? <div className="w-3 h-3 border-[1.5px] rounded-full animate-spin" style={{ borderColor: 'transparent', borderTopColor: 'currentColor' }} />
                  : <ArrowUp className="h-3 w-3" strokeWidth={2.5} />}
              </button>
            </div>
          </div>
        </form>
      </div>

    </div>
  )
}
