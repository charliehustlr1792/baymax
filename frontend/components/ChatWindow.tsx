'use client'
import { useEffect, useRef, useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { DotLottieReact } from '@lottiefiles/dotlottie-react'
import { streamChat, endSession, generateUserId, Message } from '@/lib/api'
import MessageBubble from '@/components/MessageBubble'
import ThinkingIndicator from '@/components/ThinkingIndicator'

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState(() => uuidv4())
  const userId = useRef(generateUserId())
  const bottomRef = useRef<HTMLDivElement>(null)
  const [showSavedToast, setShowSavedToast] = useState(false)

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/health`).catch(() => {})
  }, [])

  // auto end-session on tab close
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
  }, [sessionId, messages])

  // inactivity timer — 10 minutes of no messages ends session
  const inactivityTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const resetInactivityTimer = () => {
    if (inactivityTimer.current) clearTimeout(inactivityTimer.current)
    inactivityTimer.current = setTimeout(async () => {
      if (messages.length > 0) {
        await endSession(userId.current, sessionId)
        setSessionId(uuidv4()) // start fresh session
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

    // placeholder for assistant message
    setMessages(prev => [...prev, { role: 'assistant', content: '' }])

    let started = false

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
  }

  const handleEndSession = async () => {
    await endSession(userId.current, sessionId)
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
  }, [messages, isStreaming])

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
    <div className="relative h-screen overflow-hidden bg-white text-[#1A1A1A]">
      <header className="fixed inset-x-0 top-0 z-40 border-b border-[#F0F0F0] bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-24 max-w-5xl items-center justify-between px-4 sm:px-6">
          <div className="relative flex items-center gap-3">
            <div
              className={[
                'absolute transition-all duration-700 ease-in-out',
                hasMessages ? 'left-0 top-1/2 h-20 w-20 -translate-y-1/2 opacity-100' : '-left-10 top-1/2 h-0 w-0 -translate-y-1/2 opacity-0',
              ].join(' ')}
            >
              <DotLottieReact
                src="https://lottie.host/05882ab6-760b-441c-9509-cc668cad2912/45VkLzMcti.lottie"
                loop
                autoplay
              />
            </div>
            <div className={hasMessages ? 'pl-24 transition-all duration-700 ease-in-out' : 'transition-all duration-700 ease-in-out'}>
              <p className="text-2xl font-semibold tracking-tight text-[#CC0000]">Baymax</p>
              <p className="text-sm text-[#777777]">your personal healthcare companion</p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => void handleEndSession()}
            className="rounded-full border border-[#CC0000] px-5 py-2 text-sm font-medium text-[#CC0000] transition hover:bg-[#FFF4F4]"
          >
            End session
          </button>
        </div>
      </header>

      <main className="mx-auto h-full max-w-5xl px-4 pb-36 pt-28 sm:px-6">
        <div className="h-full overflow-y-auto pr-1">
          {!hasMessages && (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="h-50 w-50 transition-all duration-700 ease-in-out">
                <DotLottieReact
                  src="https://lottie.host/05882ab6-760b-441c-9509-cc668cad2912/45VkLzMcti.lottie"
                  loop
                  autoplay
                />
              </div>
              <p className="mt-4 max-w-md text-base leading-7 text-[#9A9A9A]">
                Hello. I am Baymax, your personal healthcare companion.
              </p>
            </div>
          )}

          {hasMessages && (
            <div className="space-y-4 py-3">
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
          )}
        </div>
      </main>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-[#F0F0F0] bg-white">
        <div className="mx-auto max-w-5xl px-4 py-4 sm:px-6">
          <div className="flex items-end gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder="Talk to Baymax..."
              autoFocus
              rows={1}
              className="max-h-36 min-h-12 flex-1 resize-none rounded-full border border-[#ECECEC] bg-[#FAFAFA] px-5 py-3 text-[15px] leading-6 text-[#1A1A1A] outline-none transition placeholder:text-[#A3A3A3] focus:border-[#CC0000]/40"
            />

            <button
              type="button"
              disabled={isBusy || !input.trim()}
              onClick={() => void handleSend()}
              className={[
                'grid h-12 w-12 place-items-center rounded-full text-white transition',
                isBusy || !input.trim() ? 'bg-[#D8B0B0] cursor-not-allowed' : 'bg-[#CC0000] hover:bg-[#B30000]',
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
          'fixed right-6 top-28 z-50 rounded-full bg-[#CC0000] px-4 py-2 text-sm font-medium text-white shadow-lg transition-all duration-300',
          showSavedToast ? 'translate-y-0 opacity-100' : '-translate-y-2 opacity-0 pointer-events-none',
        ].join(' ')}
      >
        Session saved
      </div>
    </div>
  )
}