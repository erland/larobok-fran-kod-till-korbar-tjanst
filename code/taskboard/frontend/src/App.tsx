import { FormEvent, useEffect, useState } from 'react'
import { taskApi, Task, TaskPriority, TaskStatus } from './api'

const statusLabels: Record<TaskStatus, string> = {
  OPEN: 'Öppen',
  IN_PROGRESS: 'Pågår',
  DONE: 'Klar'
}

const priorityLabels: Record<TaskPriority, string> = {
  LOW: 'Låg',
  NORMAL: 'Normal',
  HIGH: 'Hög'
}

export function App() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState<TaskPriority>('NORMAL')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function reload() {
    try {
      setError(null)
      setTasks(await taskApi.list())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kunde inte hämta uppgifter')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void reload()
  }, [])

  async function createTask(event: FormEvent) {
    event.preventDefault()
    if (!title.trim()) return

    try {
      const created = await taskApi.create({ title: title.trim(), priority })
      setTasks(current => [created, ...current])
      setTitle('')
      setPriority('NORMAL')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kunde inte skapa uppgiften')
    }
  }

  async function changeStatus(task: Task, status: TaskStatus) {
    try {
      const updated = await taskApi.update(task.id, {
        title: task.title,
        description: task.description,
        priority: task.priority,
        dueDate: task.dueDate,
        status
      })
      setTasks(current => current.map(item => item.id === updated.id ? updated : item))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kunde inte uppdatera uppgiften')
    }
  }

  async function removeTask(task: Task) {
    try {
      await taskApi.remove(task.id)
      setTasks(current => current.filter(item => item.id !== task.id))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Kunde inte ta bort uppgiften')
    }
  }

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">Referenstjänst</p>
        <h1>TaskBoard</h1>
        <p>En liten men komplett tjänst som följer bokens arkitektur från PWA till PostgreSQL.</p>
      </header>

      <section className="panel">
        <h2>Ny uppgift</h2>
        <form onSubmit={createTask}>
          <input
            aria-label="Titel"
            value={title}
            onChange={event => setTitle(event.target.value)}
            placeholder="Vad behöver göras?"
            maxLength={160}
          />
          <select value={priority} onChange={event => setPriority(event.target.value as TaskPriority)}>
            {Object.entries(priorityLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <button type="submit">Skapa</button>
        </form>
      </section>

      {error && <p className="error" role="alert">{error}</p>}

      <section className="panel">
        <div className="section-heading">
          <h2>Uppgifter</h2>
          <button className="secondary" onClick={() => void reload()}>Uppdatera</button>
        </div>
        {loading ? <p>Laddar…</p> : tasks.length === 0 ? <p>Inga uppgifter ännu.</p> : (
          <ul className="task-list">
            {tasks.map(task => (
              <li key={task.id}>
                <div>
                  <strong>{task.title}</strong>
                  <span>{priorityLabels[task.priority]} prioritet · {statusLabels[task.status]}</span>
                </div>
                <div className="actions">
                  <select
                    aria-label={`Status för ${task.title}`}
                    value={task.status}
                    onChange={event => void changeStatus(task, event.target.value as TaskStatus)}
                  >
                    {Object.entries(statusLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                  <button className="danger" onClick={() => void removeTask(task)}>Ta bort</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}
