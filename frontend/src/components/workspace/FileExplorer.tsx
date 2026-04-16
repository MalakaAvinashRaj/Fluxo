import { FileText, ChevronRight } from "lucide-react"

type FileType = { path: string; content: string }
type FileExplorerProps = {
  files: FileType[]
  selectedFile: string | null
  onSelectFile: (path: string) => void
}

export function FileExplorer({ files, selectedFile, onSelectFile }: FileExplorerProps) {
  const getExtLabel = (ext?: string) => {
    const colors: Record<string, string> = {
      dart: 'var(--accent)',
      yaml: 'var(--text-2)',
      md:   'var(--text-3)',
    }
    return (
      <span
        className="text-xs font-bold uppercase"
        style={{ color: colors[ext ?? ''] ?? 'var(--text-3)' }}
      >
        {ext?.slice(0, 2) ?? '—'}
      </span>
    )
  }

  const fileTree = files.reduce((tree, file) => {
    const parts = file.path.split('/')
    let current = tree
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i]
      if (!current[part]) current[part] = {}
      current = current[part]
    }
    current[parts[parts.length - 1]] = file
    return tree
  }, {} as any)

  const renderTree = (tree: any, depth = 0): React.ReactNode => {
    return Object.entries(tree).map(([name, item]) => {
      const isFile = item && typeof item === 'object' && 'path' in item
      const pl = 12 + depth * 14

      if (isFile) {
        const file = item as FileType
        const ext = file.path.split('.').pop()
        const selected = selectedFile === file.path
        return (
          <button
            key={file.path}
            onClick={() => onSelectFile(file.path)}
            style={{
              paddingLeft: pl,
              borderLeft: `1px solid ${selected ? 'var(--accent)' : 'transparent'}`,
              backgroundColor: selected ? 'var(--surface-raised)' : 'transparent',
              color: selected ? 'var(--text-1)' : 'var(--text-2)',
            }}
            className="w-full flex items-center gap-2 py-1.5 pr-3 text-left transition-colors hover:brightness-125"
          >
            <div className="w-4 flex items-center justify-center shrink-0">
              {getExtLabel(ext)}
            </div>
            <span className="text-xs truncate">{name}</span>
          </button>
        )
      }

      return (
        <div key={name}>
          <div
            style={{ paddingLeft: pl, color: 'var(--text-3)' }}
            className="flex items-center gap-1.5 py-1.5 pr-3"
          >
            <ChevronRight className="h-3 w-3 shrink-0" />
            <span className="text-xs font-semibold uppercase tracking-wider truncate">{name}</span>
          </div>
          {renderTree(item, depth + 1)}
        </div>
      )
    })
  }

  return (
    <div
      className="w-48 flex flex-col shrink-0"
      style={{ backgroundColor: 'var(--surface)', borderRight: '1px solid var(--border)' }}
    >
      <div
        className="h-11 flex items-center px-4"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <span
          className="text-xs font-semibold uppercase tracking-widest"
          style={{ color: 'var(--text-3)' }}
        >
          Files
        </span>
      </div>
      <div className="flex-1 overflow-auto py-1">
        {files.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <FileText className="h-5 w-5" style={{ color: 'var(--border-strong)' }} />
            <p className="text-xs text-center" style={{ color: 'var(--text-4)' }}>No files yet</p>
          </div>
        ) : (
          renderTree(fileTree)
        )}
      </div>
    </div>
  )
}
