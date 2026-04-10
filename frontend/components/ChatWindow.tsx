'use client'
import { useEffect, useRef, useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { DotLottieReact } from '@lottiefiles/dotlottie-react'
import { streamChat, endSession, generateUserId, Message } from '@/lib/api'
import BaymaxAvatar from '@/components/BaymaxAvatar'
import MessageBubble from '@/components/MessageBubble'
import ThinkingIndicator from '@/components/ThinkingIndicator'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState(() => uuidv4())
  const [showSavedToast, setShowSavedToast] = useState(false)
  const userId = useRef(generateUserId())
  const bottomRef = useRef<HTMLDivElement>(null)
  const inactivityTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/health`).catch(() => {})
  }, [])

  // Auto end-session on tab close.
  useEffect(() => {
    const handleUnload = () => {
      if (sessionId && messages.length > 0) {
        navigator.sendBeacon(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/end-session`,
          JSON.stringify({ user_id: userId.current, session_id: sessionId })
        )
      }
    }

    window.addEventListener('beforeunload', handleUnload)
    return () => window.removeEventListener('beforeunload', handleUnload)
  }, [messages, sessionId])

  // Ten minutes of inactivity starts a fresh session.
  const resetInactivityTimer = () => {
    if (inactivityTimer.current) clearTimeout(inactivityTimer.current)

    inactivityTimer.current = setTimeout(async () => {
      if (messages.length > 0) {
        await endSession(userId.current, sessionId).catch(() => {})
        setMessages([])
        setSessionId(uuidv4())
      }
    }, 10 * 60 * 1000)
  }

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    const userMessage: Message = { role: 'user', content: input.trim() }
    const updatedMessages = [...messages, userMessage]

    setMessages(updatedMessages)
    setInput('')
    setIsThinking(true)
    resetInactivityTimer()

    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    let started = false

    try {
      await streamChat(
        userId.current,
        sessionId,
        updatedMessages,
        (token) => {
          if (!started) {
            started = true
            setIsThinking(false)
            setIsStreaming(true)
          }

          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              role: 'assistant',
              content: updated[updated.length - 1].content + token,
            }
            return updated
          })
        },
        () => {
          setIsStreaming(false)
        }
      )
    } catch {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          role: 'assistant',
          content: 'I am here with you. Please try again in a moment.',
        }
        return updated
      })
    } finally {
      setIsThinking(false)
      setIsStreaming(false)
    }
  }

  const handleEndSession = async () => {
    await endSession(userId.current, sessionId).catch(() => {})
    setMessages([])
    setSessionId(uuidv4())
    setShowSavedToast(true)
  }

  useEffect(() => {
    if (!showSavedToast) return

    const timer = setTimeout(() => setShowSavedToast(false), 2000)
    return () => clearTimeout(timer)
  }, [showSavedToast])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [isStreaming, messages])

  useEffect(() => {
    return () => {
      if (inactivityTimer.current) clearTimeout(inactivityTimer.current)
    }
  }, [])

  const hasMessages = messages.length > 0
  const isBusy = isThinking || isStreaming

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-transparent text-[var(--foreground)]">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-[-12%] top-[-8%] h-72 w-72 rounded-full bg-[rgba(255,255,255,0.72)] blur-3xl" />
        <div className="absolute right-[-10%] top-[10%] h-80 w-80 rounded-full bg-[rgba(244,237,227,0.9)] blur-3xl" />
        <div className="absolute bottom-[-12%] left-[16%] h-96 w-96 rounded-full bg-[rgba(227,214,197,0.56)] blur-3xl" />
      </div>

      <header className="fixed inset-x-0 top-0 z-40 px-4 pt-5 sm:px-6 lg:px-8">
        <div className="mx-auto flex h-[4.75rem] max-w-6xl items-center justify-between border-b border-[var(--border)] pb-4">
          <div className="relative flex items-center gap-3">
            <div
              className={[
                'absolute transition-all duration-700 ease-in-out',
                hasMessages ? 'left-0 top-1/2 h-[4.5rem] w-[4.5rem] -translate-y-1/2 opacity-100' : '-left-8 top-1/2 h-0 w-0 -translate-y-1/2 opacity-0',
              ].join(' ')}
            >
              <DotLottieReact
                src="https://lottie.host/05882ab6-760b-441c-9509-cc668cad2912/45VkLzMcti.lottie"
                loop
                autoplay
              />
            </div>

            <div className={hasMessages ? 'pl-[5.5rem] transition-all duration-700 ease-in-out' : 'transition-all duration-700 ease-in-out'}>
              <p className="text-[2rem] leading-none font-semibold tracking-[0.01em] text-black sm:text-[2.2rem]">
                Baymax
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => void handleEndSession()}
            className="rounded-full border border-[rgba(186,164,140,0.36)] bg-[rgba(255,255,255,0.55)] px-5 py-2 text-sm font-medium text-[var(--accent-strong)] shadow-[0_10px_24px_rgba(93,79,66,0.08)] transition hover:border-[rgba(186,164,140,0.52)] hover:bg-[rgba(255,250,245,0.9)]"
          >
            End session
          </button>
        </div>
      </header>

      <main className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 pb-40 pt-[8.5rem] sm:px-6 lg:px-8">
        {!hasMessages ? (
          <section className="relative grid flex-1 items-center gap-10 py-8 lg:grid-cols-[0.92fr_1.08fr] lg:gap-6">
            <div className="order-2 max-w-2xl text-center lg:order-1 lg:text-left">
              <p className="font-script whitespace-nowrap text-[clamp(2.6rem,5.2vw,4.4rem)] leading-[1] tracking-[0.005em] text-[var(--foreground)]">
                Hello, I&apos;m Baymax
              </p>
              <p className="mt-3 text-base leading-8 text-[var(--muted)] sm:text-lg">
                Your personal health companion, and I&apos;m here to listen. What&apos;s been weighing on your mind today?
              </p>
            </div>

            <div className="order-1 flex justify-center lg:order-2 lg:justify-end">
              <div className="relative flex h-[20rem] w-[20rem] items-center justify-center sm:h-[25rem] sm:w-[25rem]">
                <div className="animate-pulse-slow absolute inset-0 rounded-full bg-[radial-gradient(circle,rgba(255,255,255,0.92)_0%,rgba(250,246,240,0.82)_45%,rgba(227,214,197,0.18)_72%,transparent_100%)]" />
                <div className="animate-drift absolute inset-[10%] rounded-full border border-white/60 bg-[rgba(255,255,255,0.4)] shadow-[0_30px_100px_rgba(93,79,66,0.12)] backdrop-blur-md" />
                <div className="absolute inset-[22%] rounded-full border border-[rgba(186,164,140,0.16)]" />
                <div className="animate-drift relative z-10 h-[72%] w-[72%]">
                  <DotLottieReact
                    src="https://lottie.host/05882ab6-760b-441c-9509-cc668cad2912/45VkLzMcti.lottie"
                    loop
                    autoplay
                  />
                </div>
              </div>
            </div>
          </section>
        ) : (
          <section className="flex min-h-0 flex-1 flex-col pt-4">
            <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-[36px] border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow)] backdrop-blur-xl">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-[linear-gradient(180deg,rgba(255,255,255,0.56),transparent)]" />
              <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-8 pt-6 sm:px-8">
                <div className="mx-auto max-w-4xl space-y-4">
                  {messages.map((message, index) => {
                    const isStreamingMessage =
                      message.role === 'assistant' &&
                      isStreaming &&
                      index === messages.length - 1

                    return (
                      <MessageBubble
                        key={`${message.role}-${index}`}
                        message={message}
                        showStreamingCursor={isStreamingMessage}
                      />
                    )
                  })}

                  {isThinking && <ThinkingIndicator />}

                  <div ref={bottomRef} />
                </div>
              </div>
            </div>
          </section>
        )}
      </main>

      <div className="fixed inset-x-0 bottom-0 z-40 px-3 pb-4 sm:px-5 sm:pb-5">
        <div className="mx-auto max-w-6xl border-t border-[var(--border)] px-1 pt-4 sm:px-2">
          <div className="flex items-end gap-3">
            <BaymaxAvatar className="hidden h-12 w-12 shrink-0 border border-[var(--border)] sm:grid" />

            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder="Talk to Baymax..."
              autoFocus
              rows={1}
              className="min-h-14 max-h-36 flex-1 resize-none rounded-[26px] border border-[var(--border)] bg-[rgba(255,255,255,0.48)] px-5 py-4 text-[15px] leading-6 text-[var(--foreground)] outline-none transition placeholder:text-[rgba(125,116,108,0.72)] focus:border-[rgba(186,164,140,0.34)] focus:bg-[rgba(255,255,255,0.82)]"
            />

            <button
              type="button"
              disabled={isBusy || !input.trim()}
              onClick={() => void handleSend()}
              className={[
                'grid h-14 w-14 place-items-center rounded-full text-white shadow-[0_18px_40px_rgba(158,134,111,0.3)] transition',
                isBusy || !input.trim()
                  ? 'cursor-not-allowed bg-[rgba(186,164,140,0.46)] shadow-none'
                  : 'bg-[linear-gradient(135deg,#baa48c_0%,#9e866f_100%)] hover:scale-[1.02] hover:brightness-105',
              ].join(' ')}
              aria-label="Send message"
            >
              <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5">
                <path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div
        className={[
          'fixed right-5 top-28 z-50 rounded-full border border-[rgba(186,164,140,0.22)] bg-[rgba(255,252,248,0.96)] px-4 py-2 text-sm font-medium text-[var(--accent-strong)] shadow-[0_18px_40px_rgba(93,79,66,0.14)] transition-all duration-300',
          showSavedToast ? 'translate-y-0 opacity-100' : '-translate-y-2 opacity-0 pointer-events-none',
        ].join(' ')}
      >
        Session saved
      </div>
    </div>
  )
}
