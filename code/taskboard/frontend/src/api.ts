export type TaskStatus = 'OPEN' | 'IN_PROGRESS' | 'DONE'
export type TaskPriority = 'LOW' | 'NORMAL' | 'HIGH'

export interface Task {
  id: string
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  dueDate: string | null
  createdAt: string
  updatedAt: string
}

export interface SaveTask {
  title: string
  description?: string | null
  status?: TaskStatus
  priority?: TaskPriority
  dueDate?: string | null
}

async function request<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers
    }
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `HTTP ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const taskApi = {
  list: () => request<Task[]>('/api/tasks'),
  create: (task: SaveTask) => request<Task>('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(task)
  }),
  update: (id: string, task: SaveTask) => request<Task>(`/api/tasks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(task)
  }),
  remove: (id: string) => request<void>(`/api/tasks/${id}`, { method: 'DELETE' })
}
