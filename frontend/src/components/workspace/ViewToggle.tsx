import { Code, Eye } from "lucide-react"

export function ViewToggle({ activeView, onViewChange }: {
  activeView: "code" | "preview"
  onViewChange: (view: "code" | "preview") => void
}) {
  return (
    <div
      className="inline-flex items-center rounded-lg p-0.5 gap-0.5"
      style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border-strong)' }}
    >
      {([
        { view: 'code', Icon: Code, label: 'Code' },
        { view: 'preview', Icon: Eye, label: 'Preview' },
      ] as const).map(({ view, Icon, label }) => (
        <button
          key={view}
          onClick={() => onViewChange(view)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150"
          style={{
            backgroundColor: activeView === view ? 'var(--surface-overlay)' : 'transparent',
            color: activeView === view ? 'var(--text-1)' : 'var(--text-3)',
          }}
        >
          <Icon className="h-3.5 w-3.5" />
          {label}
        </button>
      ))}
    </div>
  )
}
