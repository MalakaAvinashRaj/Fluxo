import { useState, useEffect, useRef } from "react"
import { Smartphone, RotateCcw, Hammer, Home, AlertCircle } from "lucide-react"

type PhonePreviewProps = {
  sessionId: string | null
  previewUrl: string | null
  isLoading?: boolean
  onRebuild?: () => void
}

export function PhonePreview({ previewUrl, isLoading = false, onRebuild }: PhonePreviewProps) {
  const [error, setError] = useState<string | null>(null)
  const [touch, setTouch] = useState({ x: 0, y: 0, show: false })
  const phoneContentRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!phoneContentRef.current) return
      const rect = phoneContentRef.current.getBoundingClientRect()
      const inBounds = e.clientX >= rect.left && e.clientX <= rect.right &&
                       e.clientY >= rect.top && e.clientY <= rect.bottom
      if (inBounds) {
        setTouch({ x: e.clientX - rect.left, y: e.clientY - rect.top, show: true })
      } else {
        setTouch(c => ({ ...c, show: false }))
      }
    }
    window.addEventListener('mousemove', onMove)
    return () => window.removeEventListener('mousemove', onMove)
  }, [])

  useEffect(() => { if (previewUrl) setError(null) }, [previewUrl])

  const handleReload = () => {
    const iframe = document.getElementById('flutter-preview') as HTMLIFrameElement
    if (iframe) iframe.src = iframe.src
  }

  const handleHome = () => {
    const iframe = document.getElementById('flutter-preview') as HTMLIFrameElement
    if (iframe && previewUrl) iframe.src = previewUrl
  }

  return (
    <div
      className="h-full flex items-center justify-center min-h-0 min-w-0 py-4 px-6"
      style={{ backgroundColor: 'var(--bg)' }}
    >
      <div className="flex items-center gap-5 self-stretch">

        {/* Phone frame — fills available height, maintains 9:19.5 ratio */}
        <div
          className="relative rounded-[3rem]"
          style={{
            height: '100%',
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border-strong)',
            boxShadow: '0 8px 40px rgba(0,0,0,0.6)',
            padding: '5px',
            aspectRatio: '9 / 19.5',
          }}
        >
          <div
            ref={phoneContentRef}
            className="w-full h-full rounded-[2.6rem] overflow-hidden relative"
            style={{ backgroundColor: 'var(--bg)', cursor: 'none' }}
          >
            {/* Touch circle cursor */}
            <div
              className="absolute pointer-events-none z-50 rounded-full transition-opacity duration-150"
              style={{
                left: touch.x - 18,
                top: touch.y - 18,
                width: 36,
                height: 36,
                border: '2px solid rgba(255,255,255,0.75)',
                backgroundColor: 'rgba(255,255,255,0.08)',
                opacity: touch.show ? 1 : 0,
                backdropFilter: 'blur(1px)',
              }}
            />
            {isLoading && !previewUrl ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div
                    className="w-8 h-8 border-2 rounded-full animate-spin mb-4 mx-auto"
                    style={{ borderColor: 'var(--accent-border)', borderTopColor: 'var(--accent)' }}
                  />
                  <p className="text-xs" style={{ color: 'var(--text-3)' }}>Building...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center p-6">
                  <AlertCircle className="w-8 h-8 mb-3 mx-auto" style={{ color: '#f87171' }} />
                  <p className="text-xs mb-4" style={{ color: '#f87171' }}>{error}</p>
                  <button
                    onClick={() => window.location.reload()}
                    className="px-3 py-1.5 text-xs rounded-lg transition-colors"
                    style={{
                      backgroundColor: 'var(--surface-raised)',
                      border: '1px solid var(--border-strong)',
                      color: 'var(--text-2)',
                    }}
                  >
                    Retry
                  </button>
                </div>
              </div>
            ) : previewUrl ? (
              <div className="relative w-full h-full">
                <iframe
                  id="flutter-preview"
                  src={previewUrl}
                  className="w-full h-full border-none"
                  title="Flutter Preview"
                />
                {isLoading && (
                  <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                    <div
                      className="flex items-center gap-2 rounded-xl px-4 py-2.5 backdrop-blur-sm"
                      style={{ backgroundColor: 'rgba(0,0,0,0.7)', border: '1px solid var(--border-strong)' }}
                    >
                      <div
                        className="w-4 h-4 border-[1.5px] rounded-full animate-spin"
                        style={{ borderColor: 'var(--accent-border)', borderTopColor: 'var(--accent)' }}
                      />
                      <span className="text-xs" style={{ color: 'var(--text-2)' }}>Rebuilding...</span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center p-6">
                  <Smartphone className="w-10 h-10 mb-3 mx-auto" style={{ color: 'var(--border-strong)' }} />
                  <p className="text-xs" style={{ color: 'var(--text-4)' }}>Preview will appear here</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Side controls */}
        <div className="flex flex-col gap-2">
          {onRebuild && (
            <SideBtn onClick={onRebuild} disabled={isLoading} icon={<Hammer className="w-3.5 h-3.5" />} label="Rebuild" accent />
          )}
          {previewUrl && (
            <SideBtn onClick={handleReload} icon={<RotateCcw className="w-3.5 h-3.5" />} label="Refresh" />
          )}
          {previewUrl && <div className="h-px mx-1" style={{ backgroundColor: 'var(--border)' }} />}
          {previewUrl && (
            <SideBtn onClick={handleHome} icon={<Home className="w-3.5 h-3.5" />} label="Home" />
          )}
          {previewUrl && (
            <div className="flex items-center gap-1.5 px-2 pt-1">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: 'var(--accent)' }} />
              <span className="text-xs" style={{ color: 'var(--text-3)' }}>Live</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function SideBtn({ onClick, disabled, icon, label, accent }: {
  onClick: () => void
  disabled?: boolean
  icon: React.ReactNode
  label: string
  accent?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition-all disabled:opacity-30"
      style={accent ? {
        backgroundColor: 'var(--accent-bg)',
        border: '1px solid var(--accent-border)',
        color: 'var(--accent)',
      } : {
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border-strong)',
        color: 'var(--text-2)',
      }}
    >
      {icon}
      {label}
    </button>
  )
}
