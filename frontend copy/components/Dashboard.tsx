"use client"
import { useState, useEffect, useRef } from 'react'
import CalendarView from './CalendarView'
import TasksView from './TasksView'
import HomeAssistantView from './HomeAssistantView'
import AiChat from './AiChat'
import BudgetView from './BudgetView'
import ShoppingList from './ShoppingList'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'

// Icons for navigation
const navigationItems = [
  { id: 'dashboard', icon: '🏠', label: 'Dashboard' },
  { id: 'calendar', icon: '📅', label: 'Calendar' },
  { id: 'tasks', icon: '✅', label: 'Tasks' },
  { id: 'shopping', icon: '🛍️', label: 'Shopping' },
  { id: 'home', icon: '💡', label: 'Smart Home' },
  { id: 'budget', icon: '💰', label: 'Budget' },
  { id: 'settings', icon: '⚙️', label: 'Settings' },
]

// Widget components
interface GoogleCalendarEvent {
  id: string
  title: string
  start: string
  end: string
  description?: string
  location?: string
  source?: string
}

interface UpcomingEvent {
  id: string
  title: string
  time: string
  type: 'work' | 'personal' | 'other'
  location?: string
}

const UpcomingEventsWidget = () => {
  const [events, setEvents] = useState<UpcomingEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const getEventType = (event: GoogleCalendarEvent): UpcomingEvent['type'] => {
    const title = event.title.toLowerCase()
    const location = (event.location || '').toLowerCase()

    if (title.includes('meeting') || title.includes('work') || title.includes('team') ||
        title.includes('project') || title.includes('standup') || title.includes('review')) {
      return 'work'
    }
    if (title.includes('lunch') || title.includes('dinner') || title.includes('coffee') ||
        title.includes('personal') || title.includes('family') || title.includes('friend')) {
      return 'personal'
    }
    return 'other'
  }

  const fetchUpcomingEvents = async () => {
    try {
      setLoading(true)
      setError(null)

      const now = new Date()
      const today = new Date()
      today.setHours(0, 0, 0, 0)

      // First, try to get today's events
      const todayEnd = new Date(today)
      todayEnd.setHours(23, 59, 59, 999)

      const todayResponse = await api.get('/events', {
        params: {
          start_date: today.toISOString().split('.')[0] + 'Z',
          end_date: todayEnd.toISOString().split('.')[0] + 'Z'
        }
      })

      const todayEvents: GoogleCalendarEvent[] = todayResponse.data.events || []

      // Check if today has more than 3 events - if so, show all today's events
      if (todayEvents.length > 3) {
        const allTodayEvents = todayEvents
          .map(event => ({
            id: event.id,
            title: event.title || 'Untitled Event',
            time: formatTime(event.start),
            type: getEventType(event),
            location: event.location,
            startTime: new Date(event.start),
            isToday: true
          }))
          .sort((a, b) => a.startTime.getTime() - b.startTime.getTime())
          .map(({startTime, ...event}) => event) // Remove startTime from final object

        setEvents(allTodayEvents)
        return
      }

      // Otherwise, get enough upcoming events to reach at least 3
      // Fetch events from now until 3 months from now to ensure we get at least 3
      const futureDate = new Date()
      futureDate.setMonth(futureDate.getMonth() + 3)

      const upcomingResponse = await api.get('/events', {
        params: {
          start_date: now.toISOString().split('.')[0] + 'Z',
          end_date: futureDate.toISOString().split('.')[0] + 'Z'
        }
      })

      const upcomingEvents: GoogleCalendarEvent[] = upcomingResponse.data.events || []

      const formattedEvents = upcomingEvents
        .map(event => {
          const eventStart = new Date(event.start)
          const isToday = eventStart.toDateString() === today.toDateString()

          return {
            id: event.id,
            title: event.title || 'Untitled Event',
            time: isToday ? formatTime(event.start) : formatTime(event.start) + ` (${eventStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })})`,
            type: getEventType(event),
            location: event.location,
            startTime: eventStart,
            isToday
          }
        })
        .filter(event => event.startTime > now) // Only future events
        .sort((a, b) => a.startTime.getTime() - b.startTime.getTime())
        .slice(0, Math.max(3, todayEvents.length)) // At least 3 events, or all today's events if more
        .map(({startTime, ...event}) => event) // Remove startTime from final object

      setEvents(formattedEvents)
    } catch (err) {
      console.error('Failed to fetch events:', err)
      setError('Failed to load events')
      setEvents([]) // Clear events on error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUpcomingEvents()
  }, [])

  if (loading) {
    return (
      <div className="widget-card h-full">
        <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
          <span>Upcoming Events</span>
          <span className="text-sm text-white/50">Loading...</span>
        </h3>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="skeleton h-16"></div>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="widget-card h-full">
        <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
          <span>Upcoming Events</span>
          <button
            onClick={fetchUpcomingEvents}
            className="text-sm text-purple-400 hover:text-purple-300"
          >
            Retry
          </button>
        </h3>
        <div className="flex items-center justify-center h-24">
          <p className="text-white/50 text-sm text-center">
            {error}<br />
            <button
              onClick={fetchUpcomingEvents}
              className="text-purple-400 hover:text-purple-300 mt-2"
            >
              Try again
            </button>
          </p>
        </div>
      </div>
    )
  }

  const typeColors: Record<UpcomingEvent['type'], string> = {
    work: 'bg-purple-500',
    personal: 'bg-blue-500',
    other: 'bg-gray-500'
  }

  const typeIcons: Record<UpcomingEvent['type'], string> = {
    work: '💼',
    personal: '👤',
    other: '📅'
  }

  // Determine header text based on display logic
  const getHeaderInfo = () => {
    if (events.length === 0) return { title: "Upcoming Events", subtitle: "None" }

    // Check if any events have dates (indicating they're from future days)
    const hasFutureEvents = events.some(event => event.time.includes('('))

    // Check if we're showing all events (because there are >3) or just upcoming
    const now = new Date()
    const hasPassedEvents = events.some(event => {
      // Try to parse the time to see if it's in the past (only for today's events)
      if (event.time.includes('(')) return false // Skip events from future days
      const eventTimeStr = event.time
      const todayDateStr = new Date().toDateString()
      const eventDateTime = new Date(`${todayDateStr} ${eventTimeStr}`)
      return eventDateTime < now
    })

    if (hasPassedEvents) {
      return { title: "Today's Events", subtitle: `All ${events.length}` }
    } else if (hasFutureEvents) {
      return { title: "Upcoming Events", subtitle: "Next 3" }
    } else {
      return { title: "Upcoming Events", subtitle: "Today" }
    }
  }

  const headerInfo = getHeaderInfo()

  return (
    <div className="widget-card h-full">
      <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
        <span>{headerInfo.title}</span>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-white/50">{headerInfo.subtitle}</span>
          <button
            onClick={fetchUpcomingEvents}
            className="text-sm text-purple-400 hover:text-purple-300"
            title="Refresh events"
          >
            🔄
          </button>
        </div>
      </h3>
      <div className="space-y-3">
        {events.length === 0 ? (
          <div className="flex items-center justify-center h-24">
            <p className="text-white/50 text-sm text-center">
              No upcoming events found
            </p>
          </div>
        ) : (
          events.map(event => {
            // Determine if this event is in the past (only applies to today's events)
            const now = new Date()
            const isFutureDay = event.time.includes('(') // Events from future days have date in parentheses
            let isPastEvent = false

            if (!isFutureDay) {
              const eventTimeStr = event.time
              const todayDateStr = new Date().toDateString()
              const eventDateTime = new Date(`${todayDateStr} ${eventTimeStr}`)
              isPastEvent = eventDateTime < now
            }

            return (
              <div key={event.id} className={`flex items-center space-x-3 p-3 rounded-lg transition-colors cursor-pointer ${
                isPastEvent ? 'bg-white/2 opacity-60' : 'bg-white/5 hover:bg-white/10'
              }`}>
                <div className={`w-1 h-12 rounded-full ${typeColors[event.type]} ${isPastEvent ? 'opacity-50' : ''}`}></div>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-sm">{typeIcons[event.type]}</span>
                    <p className={`font-medium text-sm ${isPastEvent ? 'line-through text-white/40' : ''}`}>
                      {event.title}
                    </p>
                    {isPastEvent && <span className="text-xs text-white/30">✓</span>}
                  </div>
                  <p className={`text-xs ${isPastEvent ? 'text-white/30' : 'text-white/50'}`}>
                    {event.time}
                  </p>
                  {event.location && (
                    <p className={`text-xs mt-1 ${isPastEvent ? 'text-white/25' : 'text-white/40'}`}>
                      📍 {event.location}
                    </p>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

const MiniCalendarWidget = () => {
  const [todayEventCount, setTodayEventCount] = useState<number>(0)
  const [loading, setLoading] = useState(true)

  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
  const today = new Date()
  const currentDay = today.getDay()

  // Get dates for the week
  const weekDates = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today)
    date.setDate(today.getDate() - currentDay + i)
    return date
  })

  const fetchTodayEventCount = async () => {
    try {
      setLoading(true)

      // Get today's date range
      const startOfDay = new Date(today)
      startOfDay.setHours(0, 0, 0, 0)

      const endOfDay = new Date(today)
      endOfDay.setHours(23, 59, 59, 999)

      const response = await api.get('/events', {
        params: {
          start_date: startOfDay.toISOString().split('.')[0] + 'Z',
          end_date: endOfDay.toISOString().split('.')[0] + 'Z'
        }
      })

      const events = response.data.events || []
      setTodayEventCount(events.length)
    } catch (err) {
      console.error('Failed to fetch event count:', err)
      setTodayEventCount(0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTodayEventCount()
  }, [])

  return (
    <div className="widget-card h-full">
      <h3 className="text-lg font-semibold mb-4">This Week</h3>
      <div className="grid grid-cols-7 gap-2">
        {weekDates.map((date, index) => {
          const isToday = date.toDateString() === today.toDateString()
          return (
            <div key={index} className="text-center">
              <p className="text-xs text-white/50 mb-1">{days[index]}</p>
              <div className={`
                p-2 rounded-lg cursor-pointer transition-all
                ${isToday
                  ? 'bg-purple-600 text-white font-semibold'
                  : 'bg-white/5 hover:bg-white/10'}
              `}>
                {date.getDate()}
              </div>
            </div>
          )
        })}
      </div>
      <div className="mt-4 pt-4 border-t border-white/10">
        <div className="flex items-center justify-between text-sm">
          <span className="text-white/50">Events today</span>
          {loading ? (
            <div className="skeleton w-6 h-4"></div>
          ) : (
            <span className="font-semibold text-purple-400">{todayEventCount}</span>
          )}
        </div>
      </div>
    </div>
  )
}

interface SmartDevice {
  id: number
  name: string
  type: 'light' | 'thermostat' | 'lock' | 'camera'
  status: string
  value: number | null
}

const SmartHomeWidget = () => {
  const [devices, setDevices] = useState<SmartDevice[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Mock data - replace with actual API
    setTimeout(() => {
      setDevices([
        { id: 1, name: 'Living Room Lights', type: 'light', status: 'on', value: 75 },
        { id: 2, name: 'Thermostat', type: 'thermostat', status: 'on', value: 22 },
        { id: 3, name: 'Front Door', type: 'lock', status: 'locked', value: null },
        { id: 4, name: 'Kitchen Lights', type: 'light', status: 'off', value: 0 },
      ])
      setLoading(false)
    }, 1000)
  }, [])

  if (loading) {
    return (
      <div className="widget-card h-full">
        <h3 className="text-lg font-semibold mb-4">Smart Home</h3>
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton h-24"></div>
          ))}
        </div>
      </div>
    )
  }

  const deviceIcons: Record<SmartDevice['type'], string> = {
    light: '💡',
    thermostat: '🌡️',
    lock: '🔒',
    camera: '📷',
  }

  return (
    <div className="widget-card h-full">
      <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
        <span>Smart Home</span>
        <button className="text-sm text-purple-400 hover:text-purple-300">View All</button>
      </h3>
      <div className="grid grid-cols-2 gap-3">
        {devices.map(device => (
          <div
            key={device.id}
            className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-2">
              <span className="text-2xl">{deviceIcons[device.type]}</span>
              <div className={`w-2 h-2 rounded-full ${device.status === 'on' || device.status === 'locked' ? 'bg-green-400' : 'bg-gray-400'}`}></div>
            </div>
            <p className="text-sm font-medium">{device.name}</p>
            {device.value !== null && (
              <p className="text-xs text-white/50 mt-1">
                {device.type === 'thermostat' ? `${device.value}°C` : `${device.value}%`}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// Floating AI Assistant Button
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

export default function Dashboard() {
  const [activeView, setActiveView] = useState('dashboard')
  const [sidebarExpanded, setSidebarExpanded] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)

  // Detect mobile screen
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Auto-collapse sidebar when clicking a navigation item
  const handleNavClick = (id: string) => {
    setActiveView(id)
    if (sidebarExpanded) {
      setTimeout(() => setSidebarExpanded(false), 300)
    }
  }

  // Click outside to close expanded sidebar
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sidebarExpanded && sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        setSidebarExpanded(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [sidebarExpanded])

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return (
          <div className="p-6 h-full overflow-y-auto">
            <div className="max-w-7xl mx-auto">
              {/* Header */}
              <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
                <p className="text-white/50">Here's what's happening today</p>
              </div>

              {/* Widget Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Upcoming Events */}
                <div className="lg:col-span-1">
                  <UpcomingEventsWidget />
                </div>

                {/* 7 Day Calendar */}
                <div className="lg:col-span-2">
                  <MiniCalendarWidget />
                </div>

                {/* Smart Home */}
                <div className="lg:col-span-3">
                  <SmartHomeWidget />
                </div>
              </div>
            </div>
          </div>
        )
      case 'calendar':
        return <CalendarView />
      case 'tasks':
        return <TasksView />
      case 'shopping':
        return <ShoppingList />
      case 'home':
        return <HomeAssistantView />
      case 'budget':
        return <BudgetView />
      case 'settings':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold mb-4">Settings</h2>
            <p className="text-white/50">Settings panel coming soon...</p>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="h-screen bg-black flex">
      {/* Desktop Sidebar */}
      {!isMobile && (
        <div
          ref={sidebarRef}
          className={`desktop-nav bg-black/50 backdrop-blur-xl border-r border-white/10 transition-all duration-300 ${
            sidebarExpanded ? 'w-64' : 'w-16'
          }`}
        >
          {/* Logo/Toggle */}
          <div className="p-4 border-b border-white/10">
            <button
              onClick={() => setSidebarExpanded(!sidebarExpanded)}
              className="w-full flex items-center justify-center hover:bg-white/10 rounded-lg p-2 transition-colors"
            >
              <span className="text-xl">{sidebarExpanded ? '←' : '☰'}</span>
            </button>
          </div>

          {/* Navigation */}
          <nav className="p-2">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center ${
                  sidebarExpanded ? 'justify-start' : 'justify-center'
                } px-3 py-3 mb-1 rounded-lg transition-all duration-200 ${
                  activeView === item.id
                    ? 'bg-purple-600 text-white'
                    : 'text-white/70 hover:bg-white/10 hover:text-white'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                {sidebarExpanded && (
                  <span className="ml-3 font-medium animate-fadeIn">{item.label}</span>
                )}
              </button>
            ))}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="glass-subtle border-b border-white/10 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold capitalize">{activeView}</h2>
            <div className="flex items-center space-x-4">
              <button className="icon-btn">
                <span>🔔</span>
              </button>
              <button className="icon-btn">
                <span>👤</span>
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {renderContent()}
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      {isMobile && (
        <div className="mobile-nav fixed bottom-0 left-0 right-0 glass-medium border-t border-white/20 px-2 py-2 z-40">
          <div className="flex justify-around items-center">
            {navigationItems.slice(0, 6).map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveView(item.id)}
                className={`flex flex-col items-center p-2 rounded-lg transition-colors ${
                  activeView === item.id
                    ? 'text-purple-400'
                    : 'text-white/50'
                }`}
              >
                <span className="text-xl mb-1">{item.icon}</span>
                <span className="text-xs">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Floating AI Button */}
      <FloatingAiButton />
    </div>
  )
}