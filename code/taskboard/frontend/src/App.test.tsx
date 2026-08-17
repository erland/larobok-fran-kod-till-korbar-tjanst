import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from './App'
import type { Task } from './api'

const initialTask: Task = {
  id: '11111111-1111-1111-1111-111111111111',
  title: 'Första uppgiften',
  description: null,
  status: 'OPEN',
  priority: 'NORMAL',
  dueDate: null,
  createdAt: '2026-08-17T06:00:00Z',
  updatedAt: '2026-08-17T06:00:00Z'
}

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

function textResponse(body: string, status: number) {
  return new Response(body, { status })
}

describe('TaskBoard App', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  test('laddar och visar uppgifter från API:t', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse([initialTask]))

    render(<App />)

    expect(screen.getByText('Laddar…')).toBeInTheDocument()
    expect(await screen.findByText('Första uppgiften')).toBeInTheDocument()
    expect(screen.getByText('Normal prioritet · Öppen')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/tasks', expect.any(Object))
  })

  test('skapar en uppgift från formuläret och visar resultatet', async () => {
    const user = userEvent.setup()
    const created: Task = {
      ...initialTask,
      id: '22222222-2222-2222-2222-222222222222',
      title: 'Skriv tester',
      priority: 'HIGH'
    }
    fetchMock
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(jsonResponse(created, 201))

    render(<App />)
    await screen.findByText('Inga uppgifter ännu.')

    await user.type(screen.getByLabelText('Titel'), '  Skriv tester  ')
    await user.selectOptions(screen.getByRole('combobox'), 'HIGH')
    await user.click(screen.getByRole('button', { name: 'Skapa' }))

    expect(await screen.findByText('Skriv tester')).toBeInTheDocument()
    expect(screen.getByText('Hög prioritet · Öppen')).toBeInTheDocument()
    expect(screen.getByLabelText('Titel')).toHaveValue('')

    const [, createInit] = fetchMock.mock.calls[1]
    expect(fetchMock.mock.calls[1][0]).toBe('/api/tasks')
    expect(createInit?.method).toBe('POST')
    expect(JSON.parse(String(createInit?.body))).toEqual({
      title: 'Skriv tester',
      priority: 'HIGH'
    })
  })

  test('uppdaterar status och ersätter uppgiften med API-svaret', async () => {
    const user = userEvent.setup()
    const updated: Task = {
      ...initialTask,
      status: 'DONE',
      updatedAt: '2026-08-17T06:05:00Z'
    }
    fetchMock
      .mockResolvedValueOnce(jsonResponse([initialTask]))
      .mockResolvedValueOnce(jsonResponse(updated))

    render(<App />)
    await screen.findByText('Första uppgiften')

    await user.selectOptions(screen.getByLabelText('Status för Första uppgiften'), 'DONE')

    expect(await screen.findByText('Normal prioritet · Klar')).toBeInTheDocument()
    expect(fetchMock.mock.calls[1][0]).toBe(`/api/tasks/${initialTask.id}`)
    const [, updateInit] = fetchMock.mock.calls[1]
    expect(updateInit?.method).toBe('PUT')
    expect(JSON.parse(String(updateInit?.body))).toMatchObject({
      title: 'Första uppgiften',
      priority: 'NORMAL',
      status: 'DONE'
    })
  })

  test('visar API-fel för användaren', async () => {
    fetchMock.mockResolvedValueOnce(textResponse('Backend unavailable', 503))

    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Backend unavailable')
  })
})
