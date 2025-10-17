"use client"
import { useState, useRef, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError } from '@/lib/errorHandler'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
}

const AiChat = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your personal AI assistant. I can help you with your calendar, tasks, smart home control, budget tracking, and more. How can I assist you today?",
      role: 'assistant',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const streamControllerRef = useRef<AbortController | null>(null)
  const isMountedRef = useRef(true)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    return () => {
      isMountedRef.current = false
      streamControllerRef.current?.abort()
      streamControllerRef.current = null
    }
  }, [])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    // Cancel any ongoing stream before starting a new one
    if (streamControllerRef.current) {
      streamControllerRef.current.abort()
      streamControllerRef.current = null
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      role: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    let assistantMessageId = ''
    let assistantText = ''

    try {
      assistantMessageId = `${Date.now().toString()}-assistant`
      const placeholderMessage: Message = {
        id: assistantMessageId,
        content: '',
        role: 'assistant',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, placeholderMessage])

      const conversationHistory = [...messages.slice(-5), userMessage].map(m => ({
        role: m.role,
        content: m.content
      }))

      const baseURL = api.defaults.baseURL?.replace(/\/$/, '') || ''
      const endpoint = `${baseURL}/ai/respond`

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        'X-API-Key': 'dev-api-key-12345'
      }

      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('supabase.auth.token')
        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }
      }

      const controller = new AbortController()
      streamControllerRef.current = controller

      const response = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          prompt: userMessage.content,
          conversation_history: conversationHistory
        }),
        signal: controller.signal
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      if (!response.body) {
        throw new Error('Streaming response not supported in this environment.')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      let doneStreaming = false

      const updateAssistantMessage = (delta: string) => {
        if (!delta) return
        assistantText += delta
        if (!isMountedRef.current) return
        setMessages(prev => prev.map(message => (
          message.id === assistantMessageId
            ? { ...message, content: assistantText }
            : message
        )))
      }

      while (!doneStreaming) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        let eventBoundary = buffer.indexOf('\n\n')
        while (eventBoundary !== -1) {
          const rawEvent = buffer.slice(0, eventBoundary)
          buffer = buffer.slice(eventBoundary + 2)

          const dataLines = rawEvent
            .split('\n')
            .filter(line => line.startsWith('data:'))
            .map(line => line.slice(5).trim())
            .filter(Boolean)

          if (dataLines.length) {
            const dataPayload = dataLines.join('')

            if (dataPayload === '[DONE]') {
              doneStreaming = true
              break
            }

            try {
              const parsed = JSON.parse(dataPayload)
              if (parsed?.type === 'text.delta') {
                updateAssistantMessage(parsed.content ?? '')
              } else if (parsed?.type === 'done') {
                doneStreaming = true
                break
              } else if (parsed?.type === 'error') {
                throw new Error(parsed?.message || 'Stream error received.')
              }
            } catch (streamError) {
              console.error('Failed to parse stream event:', streamError)
            }
          }

          eventBoundary = buffer.indexOf('\n\n')
        }
      }

      // Flush any remaining buffered content
      if (buffer.trim().length) {
        const dataLines = buffer
          .split('\n')
          .filter(line => line.startsWith('data:'))
          .map(line => line.slice(5).trim())
          .filter(Boolean)
        if (dataLines.length) {
          const dataPayload = dataLines.join('')
          try {
            const parsed = JSON.parse(dataPayload)
            if (parsed?.type === 'text.delta') {
              updateAssistantMessage(parsed.content ?? '')
            }
          } catch (flushError) {
            console.error('Failed to parse final stream chunk:', flushError)
          }
        }
      }

      if (!assistantText) {
        updateAssistantMessage("I'm sorry, I couldn't process that request.")
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }

      console.error('AI chat error:', error)

      if (assistantMessageId && isMountedRef.current) {
        setMessages(prev => prev.filter(message => message.id !== assistantMessageId))
      }

      const errorContent = error instanceof Error ? error.message : handleApiError(error)

      if (isMountedRef.current) {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: `Sorry, I encountered an error: ${errorContent}`,
          role: 'assistant',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
    } finally {
      streamControllerRef.current = null
      if (isMountedRef.current) {
        setIsLoading(false)
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const suggestedPrompts = [
    { icon: '📅', text: "What's on my calendar today?" },
    { icon: '✅', text: "Show me my pending tasks" },
    { icon: '💡', text: "Turn off all lights" },
    { icon: '💰', text: "How's my budget this month?" },
  ]

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  return (
    <div className="flex flex-col h-full bg-black">
      {/* Chat Header */}
      <div className="glass-subtle border-b border-white/10 p-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center">
            <span className="text-xl">✨</span>
          </div>
          <div>
            <h2 className="text-lg font-semibold">AI Assistant</h2>
            <p className="text-sm text-white/50">Always here to help</p>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
          >
            <div className={`max-w-[70%] ${message.role === 'user' ? 'order-2' : 'order-1'}`}>
              <div className="flex items-end space-x-2">
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm">✨</span>
                  </div>
                )}
                <div>
                  <div className={`rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-purple-600 text-white'
                      : 'glass-subtle text-white'
                  }`}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                  <p className={`text-xs text-white/30 mt-1 ${
                    message.role === 'user' ? 'text-right' : 'text-left ml-10'
                  }`}>
                    {formatTime(message.timestamp)}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                    <span className="text-sm">👤</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start animate-fadeIn">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center">
                <span className="text-sm">✨</span>
              </div>
              <div className="glass-subtle rounded-2xl px-4 py-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-white/50 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-white/50 rounded-full animate-pulse delay-100"></div>
                  <div className="w-2 h-2 bg-white/50 rounded-full animate-pulse delay-200"></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      {messages.length === 1 && (
        <div className="px-4 pb-2">
          <p className="text-sm text-white/50 mb-3">Try asking:</p>
          <div className="grid grid-cols-2 gap-2">
            {suggestedPrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => setInput(prompt.text)}
                className="glass-subtle rounded-xl p-3 text-left hover:bg-white/10 transition-colors group"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{prompt.icon}</span>
                  <span className="text-sm text-white/70 group-hover:text-white">
                    {prompt.text}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="glass-subtle border-t border-white/10 p-4">
        <div className="flex items-end space-x-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              className="input w-full resize-none min-h-[48px] max-h-[120px] pr-12"
              rows={1}
              disabled={isLoading}
              style={{
                height: 'auto',
                overflow: 'hidden'
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement
                target.style.height = 'auto'
                target.style.height = `${target.scrollHeight}px`
              }}
            />
            <div className="absolute right-2 bottom-2 flex items-center space-x-2">
              <button className="icon-btn w-8 h-8 text-white/50 hover:text-white">
                <span>📎</span>
              </button>
            </div>
          </div>
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all ${
              input.trim() && !isLoading
                ? 'bg-purple-600 text-white hover:bg-purple-700 active:scale-95'
                : 'bg-white/10 text-white/30 cursor-not-allowed'
            }`}
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <span className="text-xl">↑</span>
            )}
          </button>
        </div>
        <p className="text-xs text-white/30 mt-2 text-center">
          AI Assistant can help with calendar, tasks, smart home, and budget management
        </p>
      </div>
    </div>
  )
}

export default AiChat