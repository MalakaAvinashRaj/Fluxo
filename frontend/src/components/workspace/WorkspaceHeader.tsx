import { Share, Settings, Download, Zap } from "lucide-react"
import { ViewToggle } from "./ViewToggle"

export function WorkspaceHeader({ activeView, onViewChange }: {
  activeView: "code" | "preview";
  onViewChange: (view: "code" | "preview") => void;
}) {
  return (
    <header
      className="h-11 flex items-center justify-between px-4 shrink-0"
      style={{ backgroundColor: 'var(--bg)', borderBottom: '1px solid var(--border)', boxShadow: '0 1px 8px rgba(0,0,0,0.08)' }}
    >
      {/* Left */}
      <div className="flex items-center gap-3">
        <a href="/" className="flex items-center gap-2">
          <Zap className="h-4 w-4" style={{ color: 'var(--accent)' }} strokeWidth={2.5} />
          <span className="text-sm font-semibold tracking-tight" style={{ color: 'var(--text-1)' }}>
            Fluxo
          </span>
        </a>
        <div className="h-4 w-px" style={{ backgroundColor: 'var(--border-strong)' }} />
        <span className="text-xs" style={{ color: 'var(--text-3)' }}>Workspace</span>
      </div>

      {/* Center */}
      <ViewToggle activeView={activeView} onViewChange={onViewChange} />

      {/* Right */}
      <div className="flex items-center gap-1">
        {[
          { icon: Share, label: 'Share' },
          { icon: Settings, label: 'Settings' },
          { icon: Download, label: 'Download' },
        ].map(({ icon: Icon, label }) => (
          <button
            key={label}
            title={label}
            onClick={() => alert(`${label} coming soon`)}
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors"
            style={{ color: 'var(--text-3)' }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--text-1)', e.currentTarget.style.backgroundColor = 'var(--surface-raised)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-3)', e.currentTarget.style.backgroundColor = 'transparent')}
          >
            <Icon className="h-3.5 w-3.5" />
          </button>
        ))}
      </div>
    </header>
  )
}
