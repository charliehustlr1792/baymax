import { v4 as uuidv4 } from 'uuid'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function generateSessionId(): string {
  return uuidv4()
}

export function generateUserId(): string {
  if (typeof window === 'undefined') return uuidv4()
  const stored = localStorage.getItem('echomind_user_id')
  if (stored) return stored
  const newId = uuidv4()
  localStorage.setItem('echomind_user_id', newId)
  return newId
}

export async function streamChat(
  userId: string,
  sessionId: string,
  messages: Message[],
  onToken: (token: string) => void,
  onDone: () => void
): Promise<void> {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL

  const response = await fetch(`${backendUrl}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      messages,
    }),
  })

  if (!response.body) throw new Error('No response body')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.token) onToken(data.token)
        if (data.done) onDone()
      } catch {
        continue
      }
    }
  }
}

export async function endSession(
  userId: string,
  sessionId: string
): Promise<void> {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL
  await fetch(`${backendUrl}/end-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, session_id: sessionId }),
  })
}