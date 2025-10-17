"use client"
import { useState, useEffect, useRef } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'

const FloatingAiButton = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [chatHistory, setChatHistory] = useState<Array<{id: string, message: string, response: string, timestamp: Date}>>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || isLoading) return

    const userMessage = message.trim()
    setMessage('')
    setIsLoading(true)

    try {
      const response = await api.post('/ai/conversation', { message: userMessage })
      const aiResponse = response.data.response || 'No response received'

      // Add to chat history
      const newChatEntry = {
        id: Date.now().toString(),
        message: userMessage,
        response: aiResponse,
        timestamp: new Date()
      }
      setChatHistory(prev => [...prev, newChatEntry])

    } catch (error) {
      showToast(handleApiError(error), 'error')
      // Add error to chat history
      const errorEntry = {
        id: Date.now().toString(),
        message: userMessage,
        response: `Error: ${handleApiError(error)}`,
        timestamp: new Date()
      }
      setChatHistory(prev => [...prev, errorEntry])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      {/* AI Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-purple-600 rounded-full shadow-lg hover:bg-purple-700 transition-all duration-200 flex items-center justify-center group hover:scale-110 active:scale-95"
      >
        <span className="text-2xl">✨</span>
      </button>

      {/* AI Chat Interface */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 animate-slideIn">
          <div className="glass-medium rounded-2xl shadow-2xl w-96 h-[500px] flex flex-col">
            {/* Chat Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/10">
              <div className="flex items-center space-x-3">
                <span className="text-xl">✨</span>
                <h4 className="font-semibold">AI Assistant</h4>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatHistory.length === 0 ? (
                <div className="text-center text-gray-400 py-8">
                  <span className="text-2xl block mb-2">💬</span>
                  <p>Start a conversation with your AI assistant!</p>
                </div>
              ) : (
                chatHistory.map((chat) => (
                  <div key={chat.id} className="space-y-3">
                    {/* User Message */}
                    <div className="flex justify-end">
                      <div className="bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-2 max-w-[80%]">
                        <p className="text-sm">{chat.message}</p>
                        <p className="text-xs opacity-70 mt-1">
                          {chat.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>

                    {/* AI Response */}
                    <div className="flex justify-start">
                      <div className="bg-gray-700 text-white rounded-2xl rounded-bl-md px-4 py-2 max-w-[80%]">
                        <p className="text-sm whitespace-pre-wrap">{chat.response}</p>
                        <p className="text-xs opacity-70 mt-1">
                          AI • {chat.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}

              {/* Loading indicator */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-700 text-white rounded-2xl rounded-bl-md px-4 py-2">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      <span className="text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Chat Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-white/10">
              <div className="flex space-x-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Ask me anything..."
                  className="input flex-1 text-sm"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !message.trim()}
                  className="btn-primary text-sm px-4"
                >
                  Send
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

export default FloatingAiButton

