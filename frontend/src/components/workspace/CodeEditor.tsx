import { useState, useEffect } from "react"
import { Copy, Download, FileCode } from "lucide-react"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism"

export type CodeEditorProps = {
  files?: Array<{ path: string; content: string }>
  selectedFile?: string | null
  onSelectFile?: (path: string) => void
}

function getLanguage(filePath: string): string {
  const ext = filePath.split('.').pop()
  const map: Record<string, string> = {
    dart: 'dart',
    yaml: 'yaml',
    yml: 'yaml',
    json: 'json',
    md: 'markdown',
    ts: 'typescript',
    tsx: 'tsx',
    js: 'javascript',
  }
  return map[ext ?? ''] ?? 'text'
}

// Override vscDarkPlus to use our CSS variables for the background
const editorTheme = {
  ...vscDarkPlus,
  'pre[class*="language-"]': {
    ...vscDarkPlus['pre[class*="language-"]'],
    background: 'transparent',
    margin: 0,
    padding: 0,
    fontSize: '12px',
    lineHeight: '1.6',
    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, Monaco, Consolas, monospace',
  },
  'code[class*="language-"]': {
    ...vscDarkPlus['code[class*="language-"]'],
    background: 'transparent',
    fontSize: '12px',
    lineHeight: '1.6',
    fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, Monaco, Consolas, monospace',
  },
}

export function CodeEditor({ files = [], selectedFile: propSelectedFile = null, onSelectFile }: CodeEditorProps) {
  const [internalSelectedFile, setInternalSelectedFile] = useState<string | null>(null)
  const selectedFile = propSelectedFile || internalSelectedFile
  const [fileContent, setFileContent] = useState<string>("")
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (files.length > 0 && !selectedFile) {
      const mainFile = files.find(f => f.path === "lib/main.dart") || files[0]
      onSelectFile ? onSelectFile(mainFile.path) : setInternalSelectedFile(mainFile.path)
    }
  }, [files, selectedFile, onSelectFile])

  useEffect(() => {
    if (selectedFile) {
      const file = files.find(f => f.path === selectedFile)
      if (file) setFileContent(file.content)
    }
  }, [selectedFile, files])

  const copyToClipboard = () => {
    navigator.clipboard.writeText(fileContent)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const downloadFile = () => {
    if (!selectedFile || !fileContent) return
    const blob = new Blob([fileContent], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = selectedFile.split("/").pop() || "file.txt"
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex-1 h-full flex flex-col" style={{ backgroundColor: 'var(--bg)' }}>

      {/* Tab bar */}
      <div
        className="h-11 flex items-center justify-between px-4 shrink-0"
        style={{ backgroundColor: 'var(--surface)', borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex items-center gap-2">
          {selectedFile ? (
            <>
              <FileCode className="h-3.5 w-3.5" style={{ color: 'var(--accent)' }} />
              <span className="text-xs font-medium" style={{ color: 'var(--text-2)' }}>{selectedFile}</span>
            </>
          ) : (
            <span className="text-xs" style={{ color: 'var(--text-4)' }}>No file selected</span>
          )}
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={copyToClipboard}
            disabled={!fileContent}
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors disabled:opacity-30"
            style={{
              backgroundColor: 'var(--surface-raised)',
              border: '1px solid var(--border)',
              color: copied ? 'var(--accent)' : 'var(--text-3)',
            }}
            title={copied ? 'Copied!' : 'Copy'}
          >
            <Copy className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={downloadFile}
            disabled={!fileContent}
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors disabled:opacity-30"
            style={{ backgroundColor: 'var(--surface-raised)', border: '1px solid var(--border)', color: 'var(--text-3)' }}
            title="Download"
          >
            <Download className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {files.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 mx-auto"
                style={{ backgroundColor: 'var(--surface-raised)', border: '1px solid var(--border)' }}
              >
                <FileCode className="h-5 w-5" style={{ color: 'var(--text-4)' }} />
              </div>
              <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-2)' }}>No files to display</p>
              <p className="text-xs" style={{ color: 'var(--text-4)' }}>Generate an app first to see the code</p>
            </div>
          </div>
        ) : (
          <div className="p-5" style={{ backgroundColor: 'var(--bg)' }}>
            {/* Line numbers + highlighted code */}
            <SyntaxHighlighter
              language={getLanguage(selectedFile ?? '')}
              style={editorTheme}
              showLineNumbers
              lineNumberStyle={{
                color: 'var(--text-4)',
                fontSize: '11px',
                paddingRight: '20px',
                minWidth: '2.5em',
                userSelect: 'none',
              }}
              customStyle={{
                background: 'transparent',
                padding: 0,
                margin: 0,
                overflowX: 'visible',
              }}
              wrapLines
              wrapLongLines={false}
            >
              {fileContent}
            </SyntaxHighlighter>
          </div>
        )}
      </div>
    </div>
  )
}
