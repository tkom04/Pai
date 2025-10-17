"use client"
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/router'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'

export default function Home() {
  const router = useRouter()
  const [greeting, setGreeting] = useState('')
  const [timeOfDay, setTimeOfDay] = useState<'morning' | 'afternoon' | 'evening'>('morning')
  const [stats, setStats] = useState({
    eventsCount: 0,
    tasksCount: 0,
    shoppingItemsCount: 0,
    loading: true
  })
  const [aiMessage, setAiMessage] = useState('')
  const [aiLoading, setAiLoading] = useState(false)
  const [aiResponse, setAiResponse] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  // Determine greeting based on time
  useEffect(() => {
    const hour = new Date().getHours()
    let period: 'morning' | 'afternoon' | 'evening'

    if (hour < 12) {
      period = 'morning'
      setGreeting('Good morning')
    } else if (hour < 18) {
      period = 'afternoon'
      setGreeting('Good afternoon')
    } else {
      period = 'evening'
      setGreeting('Good evening')
    }

    setTimeOfDay(period)
  }, [])

  // Fetch quick stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const now = new Date()
        const hour = now.getHours()

        // Determine date range based on time of day
        let startDate: Date
        let endDate: Date

        if (hour < 18) {
          // Before 6 PM - show today's events
          startDate = new Date(now)
          startDate.setHours(0, 0, 0, 0)
          endDate = new Date(now)
          endDate.setHours(23, 59, 59, 999)
        } else {
          // After 6 PM - show tomorrow's events
          startDate = new Date(now)
          startDate.setDate(startDate.getDate() + 1)
          startDate.setHours(0, 0, 0, 0)
          endDate = new Date(startDate)
          endDate.setHours(23, 59, 59, 999)
        }

        // Fetch events (IMPORTANT: Backend expects 'start' and 'end', not 'start_date' and 'end_date')
        const eventsResponse = await api.get('/events', {
          params: {
            start: startDate.toISOString(),
            end: endDate.toISOString()
          }
        })

        const allEvents = eventsResponse.data.events || []

        // Helper function to check if event is within target date range
        const isInTargetRange = (dateString: string) => {
          const date = new Date(dateString)
          const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate())
          const targetDateOnly = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate())
          return dateOnly.getTime() === targetDateOnly.getTime()
        }

        // Filter to only events where start OR end date is in the target range
        const filteredEvents = allEvents.filter((event: any) =>
          isInTargetRange(event.start) || isInTargetRange(event.end)
        )

        // Fetch tasks
        const tasksResponse = await api.get('/tasks')
        const incompleteTasks = (tasksResponse.data.tasks || []).filter((task: any) => task.status !== 'done' && task.status !== 'archived')

        // Fetch shopping items
        const shoppingResponse = await api.get('/groceries')
        const uncheckedItems = (shoppingResponse.data.items || []).filter((item: any) => !item.checked)

        setStats({
          eventsCount: filteredEvents.length || 0,
          tasksCount: incompleteTasks.length || 0,
          shoppingItemsCount: uncheckedItems.length || 0,
          loading: false
        })
      } catch (error) {
        console.error('Failed to fetch stats:', error)
        setStats(prev => ({ ...prev, loading: false }))
      }
    }

    fetchStats()
  }, [])

  const getEventTimeLabel = () => {
    const hour = new Date().getHours()
    return hour < 18 ? 'today' : 'tomorrow'
  }

  const handleAiSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!aiMessage.trim() || aiLoading) return

    const userMessage = aiMessage.trim()
    setAiMessage('')
    setAiLoading(true)

    try {
      const response = await api.post('/ai/conversation', { message: userMessage })
      const aiReply = response.data.response || 'No response received'
      setAiResponse(aiReply)
    } catch (error) {
      showToast(handleApiError(error), 'error')
      setAiResponse('Sorry, I encountered an error. Please try again.')
    } finally {
      setAiLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6 overflow-hidden relative">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-4xl w-full">
        {/* Greeting */}
        <div className="text-center mb-12 animate-fadeIn">
          <h1 className="text-6xl font-bold mb-4 gradient-text">
            {greeting}
          </h1>
          <p className="text-2xl text-white/70">Welcome back to your orbit</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Events Card */}
          <div className="glass-medium rounded-2xl p-6 hover:scale-105 transition-all duration-300 animate-slideIn">
            <div className="flex items-center justify-between mb-4">
              <span className="text-4xl">📅</span>
              {stats.loading ? (
                <div className="skeleton w-12 h-8"></div>
              ) : (
                <span className="text-4xl font-bold text-purple-400">{stats.eventsCount}</span>
              )}
            </div>
            <p className="text-white/70 text-sm">
              {stats.eventsCount === 1 ? 'Event' : 'Events'} {getEventTimeLabel()}
            </p>
          </div>

          {/* Tasks Card */}
          <div className="glass-medium rounded-2xl p-6 hover:scale-105 transition-all duration-300 animate-slideIn" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center justify-between mb-4">
              <span className="text-4xl">✅</span>
              {stats.loading ? (
                <div className="skeleton w-12 h-8"></div>
              ) : (
                <span className="text-4xl font-bold text-blue-400">{stats.tasksCount}</span>
              )}
            </div>
            <p className="text-white/70 text-sm">
              {stats.tasksCount === 1 ? 'Task' : 'Tasks'} pending
            </p>
          </div>

          {/* Shopping Card */}
          <div className="glass-medium rounded-2xl p-6 hover:scale-105 transition-all duration-300 animate-slideIn" style={{ animationDelay: '0.2s' }}>
            <div className="flex items-center justify-between mb-4">
              <span className="text-4xl">🛍️</span>
              {stats.loading ? (
                <div className="skeleton w-12 h-8"></div>
              ) : (
                <span className="text-4xl font-bold text-green-400">{stats.shoppingItemsCount}</span>
              )}
            </div>
            <p className="text-white/70 text-sm">
              {stats.shoppingItemsCount === 1 ? 'Item' : 'Items'} to buy
            </p>
          </div>
        </div>

        {/* Quick AI Chat */}
        <div className="mb-12 animate-slideIn" style={{ animationDelay: '0.3s' }}>
          <div className="glass-medium rounded-2xl p-6 max-w-2xl mx-auto">
            <div className="flex items-center space-x-3 mb-4">
              <span className="text-3xl">✨</span>
              <h3 className="text-xl font-semibold">Quick AI Chat</h3>
            </div>

            <form onSubmit={handleAiSubmit} className="space-y-4">
              <div className="flex space-x-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={aiMessage}
                  onChange={(e) => setAiMessage(e.target.value)}
                  placeholder="Ask me anything... (e.g., What's on my schedule today?)"
                  className="input flex-1"
                  disabled={aiLoading}
                />
                <button
                  type="submit"
                  disabled={aiLoading || !aiMessage.trim()}
                  className="btn-primary px-6"
                >
                  {aiLoading ? '...' : 'Ask'}
                </button>
              </div>

              {aiResponse && (
                <div className="glass-subtle rounded-xl p-4 animate-fadeIn">
                  <div className="flex items-start space-x-3">
                    <span className="text-xl">🤖</span>
                    <div className="flex-1">
                      <p className="text-sm text-white/90 whitespace-pre-wrap">{aiResponse}</p>
                    </div>
                  </div>
                </div>
              )}
            </form>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center">
          <button
            onClick={() => router.push('/dashboard')}
            className="group relative inline-flex items-center justify-center px-12 py-4 text-lg font-medium text-white bg-gradient-to-r from-purple-600 to-blue-600 rounded-full overflow-hidden transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/50"
          >
            <span className="relative z-10 flex items-center space-x-3">
              <span>Go to Dashboard</span>
              <span className="transform group-hover:translate-x-1 transition-transform">→</span>
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-purple-700 to-blue-700 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>
        </div>

        {/* Time-based Message */}
        <div className="mt-8 text-center">
          <p className="text-white/50 text-sm">
            {timeOfDay === 'morning' && "Let's make today productive! ☀️"}
            {timeOfDay === 'afternoon' && "Keep up the great work! 🌤️"}
            {timeOfDay === 'evening' && "Time to wind down and plan ahead! 🌙"}
          </p>
        </div>
      </div>
    </div>
  )
}
