"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'

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

  const fetchTodayEvents = async () => {
    try {
      setLoading(true)
      setError(null)

      const today = new Date()
      today.setHours(0, 0, 0, 0)

      const todayEnd = new Date(today)
      todayEnd.setHours(23, 59, 59, 999)

      // IMPORTANT: Backend expects 'start' and 'end', not 'start_date' and 'end_date'
      const response = await api.get('/events', {
        params: {
          start: today.toISOString(),
          end: todayEnd.toISOString()
        }
      })

      const allEvents: GoogleCalendarEvent[] = response.data.events || []

      // Helper function to check if a date is today
      const isToday = (dateString: string) => {
        const date = new Date(dateString)
        const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate())
        const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate())
        return dateOnly.getTime() === todayOnly.getTime()
      }

      // Filter to only events where start OR end date is today
      const todayEvents = allEvents.filter(event =>
        isToday(event.start) || isToday(event.end)
      )

      const formattedEvents = todayEvents
        .map(event => ({
          id: event.id,
          title: event.title || 'Untitled Event',
          time: formatTime(event.start),
          type: getEventType(event),
          location: event.location,
          startTime: new Date(event.start)
        }))
        .sort((a, b) => a.startTime.getTime() - b.startTime.getTime())
        .map(({startTime, ...event}) => event) // Remove startTime from final object

      setEvents(formattedEvents)
    } catch (err) {
      console.error('Failed to fetch events:', err)
      setError('Failed to load events')
      setEvents([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTodayEvents()
  }, [])

  if (loading) {
    return (
      <div className="widget-card h-full">
        <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
          <span>Today's Events</span>
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
          <span>Today's Events</span>
          <button
            onClick={fetchTodayEvents}
            className="text-sm text-purple-400 hover:text-purple-300"
          >
            Retry
          </button>
        </h3>
        <div className="flex items-center justify-center h-24">
          <p className="text-white/50 text-sm text-center">
            {error}<br />
            <button
              onClick={fetchTodayEvents}
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

  return (
    <div className="widget-card h-full">
      <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
        <span>Today's Events</span>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-white/50">{events.length}</span>
          <button
            onClick={fetchTodayEvents}
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
              No events today
            </p>
          </div>
        ) : (
          events.map(event => {
            // Determine if this event is in the past
            const now = new Date()
            const eventTimeStr = event.time
            const todayDateStr = new Date().toDateString()
            const eventDateTime = new Date(`${todayDateStr} ${eventTimeStr}`)
            const isPastEvent = eventDateTime < now

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

export default UpcomingEventsWidget

