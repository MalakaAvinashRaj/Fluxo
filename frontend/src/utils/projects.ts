export type Project = {
  projectId: string
  name: string
  sessionId: string
  previewUrl: string | null
  createdAt: string
  pinned?: boolean
  files?: { path: string; content: string }[]
}

const STORAGE_KEY = 'ras_projects'

function getAll(): Project[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function save(projects: Project[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(projects))
}

export function createProject(projectId: string, sessionId: string, name: string): Project {
  const project: Project = {
    projectId,
    name,
    sessionId,
    previewUrl: null,
    createdAt: new Date().toISOString(),
  }
  save([project, ...getAll()])
  return project
}

export function getProject(projectId: string): Project | null {
  return getAll().find(p => p.projectId === projectId) ?? null
}

export function updateProject(
  projectId: string,
  updates: Partial<Pick<Project, 'previewUrl' | 'name' | 'sessionId' | 'files' | 'pinned'>>
): void {
  save(getAll().map(p => (p.projectId === projectId ? { ...p, ...updates } : p)))
}

export function getAllProjects(): Project[] {
  return getAll()
}

export function deleteProject(projectId: string): void {
  save(getAll().filter(p => p.projectId !== projectId))
}
