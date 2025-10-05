"use client"
import { useState, useEffect } from "react"
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'
import { Card, ListItem } from './ui/Card'

interface Event {
  id: string
  title: string
  start: string
  end: string
  description?: string
  location?: string
  attendees?: Array<{ email: string }>
}

type CalendarViewType = 'month' | 'week' | 'day'

export default function CalendarView() {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [currentDate, setCurrentDate] = useState(new Date())
  const [view, setView] = useState<CalendarViewType>('week')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)

  const [newEvent, setNewEvent] = useState({
    summary: '',
    date: '',
    startTime: '',
    endTime: '',
    description: '',
    location: ''
  })

  useEffect(() => {
    fetchEvents()
  }, [currentDate, view])

  const fetchEvents = async () => {
    setLoading(true)
    try {
      const response = await api.get('/events')
      setEvents(response.data.events || [])
    } catch (error) {
      showToast(`Failed to fetch events: ${handleApiError(error)}`, 'error')
      setEvents([])
    } finally {
      setLoading(false)
    }
  }

  const createEvent = async () => {
    if (!newEvent.summary || !newEvent.date || !newEvent.startTime) {
      showToast('Please fill in required fields', 'error')
      return
    }

    try {
      const startDateTime = `${newEvent.date}T${newEvent.startTime}:00`
      const endDateTime = newEvent.endTime
        ? `${newEvent.date}T${newEvent.endTime}:00`
        : `${newEvent.date}T${newEvent.startTime.split(':')[0]}:${parseInt(newEvent.startTime.split(':')[1]) + 30}:00`

      await api.post('/create_event', {
        title: newEvent.summary,
        start: startDateTime,
        end: endDateTime,
        description: newEvent.description,
        location: newEvent.location
      })

      showToast('Event created successfully', 'success')
      setShowCreateModal(false)
      setNewEvent({
        summary: '',
        date: '',
        startTime: '',
        endTime: '',
        description: '',
        location: ''
      })
      fetchEvents()
    } catch (error) {
      showToast(`Failed to create event: ${handleApiError(error)}`, 'error')
    }
  }

  const deleteEvent = async (eventId: string) => {
    try {
      await api.delete(`/events/${eventId}`)
      showToast('Event deleted successfully', 'success')
      setSelectedEvent(null)
      fetchEvents()
    } catch (error) {
      showToast(`Failed to delete event: ${handleApiError(error)}`, 'error')
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    })
  }

  const getEventType = (event: Event) => {
    if (event.location?.toLowerCase().includes('zoom') ||
        event.location?.toLowerCase().includes('meet') ||
        event.location?.toLowerCase().includes('teams')) {
      return { icon: '💻', color: 'bg-blue-500' }
    }
    if (event.title.toLowerCase().includes('meeting')) {
      return { icon: '👥', color: 'bg-purple-500' }
    }
    if (event.title.toLowerCase().includes('lunch') ||
        event.title.toLowerCase().includes('dinner')) {
      return { icon: '🍽️', color: 'bg-green-500' }
    }
    return { icon: '📅', color: 'bg-gray-500' }
  }

  // Get week dates
  const getWeekDates = () => {
    const startOfWeek = new Date(currentDate)
    const day = startOfWeek.getDay()
    startOfWeek.setDate(startOfWeek.getDate() - day)

    return Array.from({ length: 7 }, (_, i) => {
      const date = new Date(startOfWeek)
      date.setDate(startOfWeek.getDate() + i)
      return date
    })
  }

  // Get month dates
  const getMonthDates = () => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const startDate = new Date(firstDay)
    const endDate = new Date(lastDay)

    // Start from Sunday of the week containing the first day
    startDate.setDate(startDate.getDate() - startDate.getDay())

    // End on Saturday of the week containing the last day
    endDate.setDate(endDate.getDate() + (6 - endDate.getDay()))

    const dates = []
    const current = new Date(startDate)

    while (current <= endDate) {
      dates.push(new Date(current))
      current.setDate(current.getDate() + 1)
    }

    return dates
  }

  // Navigation functions
  const navigatePrevious = () => {
    const newDate = new Date(currentDate)
    if (view === 'day') {
      newDate.setDate(newDate.getDate() - 1)
    } else if (view === 'week') {
      newDate.setDate(newDate.getDate() - 7)
    } else if (view === 'month') {
      newDate.setMonth(newDate.getMonth() - 1)
    }
    setCurrentDate(newDate)
  }

  const navigateNext = () => {
    const newDate = new Date(currentDate)
    if (view === 'day') {
      newDate.setDate(newDate.getDate() + 1)
    } else if (view === 'week') {
      newDate.setDate(newDate.getDate() + 7)
    } else if (view === 'month') {
      newDate.setMonth(newDate.getMonth() + 1)
    }
    setCurrentDate(newDate)
  }

  const goToToday = () => {
    setCurrentDate(new Date())
  }

  const weekDates = getWeekDates()
  const monthDates = getMonthDates()
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div className="flex items-center space-x-4">
            <div>
              <h1 className="text-3xl font-bold mb-2">Calendar</h1>
              <p className="text-white/50">
                {view === 'day' && currentDate.toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric'
                })}
                {view === 'week' && (() => {
                  const startOfWeek = new Date(currentDate)
                  startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay())
                  const endOfWeek = new Date(startOfWeek)
                  endOfWeek.setDate(endOfWeek.getDate() + 6)
                  return `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
                })()}
                {view === 'month' && currentDate.toLocaleDateString('en-US', {
                  month: 'long',
                  year: 'numeric'
                })}
              </p>
            </div>
            {/* Navigation */}
            <div className="flex items-center space-x-2">
              <button
                onClick={navigatePrevious}
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
              >
                ←
              </button>
              <button
                onClick={goToToday}
                className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm"
              >
                Today
              </button>
              <button
                onClick={navigateNext}
                className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
              >
                →
              </button>
            </div>
          </div>
          <div className="flex items-center space-x-3 mt-4 md:mt-0">
            {/* View Selector */}
            <div className="flex bg-white/5 rounded-lg p-1">
              {(['day', 'week', 'month'] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    view === v
                      ? 'bg-purple-600 text-white'
                      : 'text-white/70 hover:text-white'
                  }`}
                >
                  {v.charAt(0).toUpperCase() + v.slice(1)}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              + New Event
            </button>
          </div>
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Calendar View */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              {/* Day View */}
              {view === 'day' && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">
                    {currentDate.toLocaleDateString('en-US', {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </h3>
                  {loading ? (
                    <div className="space-y-3">
                      {[1, 2, 3, 4, 5].map(i => (
                        <div key={i} className="skeleton h-16"></div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {events
                        .filter(event => {
                          const eventDate = new Date(event.start)
                          return eventDate.toDateString() === currentDate.toDateString()
                        })
                        .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
                        .map(event => {
                          const eventType = getEventType(event)
                          return (
                            <ListItem
                              key={event.id}
                              title={event.title}
                              subtitle={`${formatTime(event.start)} - ${formatTime(event.end)}`}
                              icon={eventType.icon}
                              onClick={() => setSelectedEvent(event)}
                              rightElement={
                                <div className={`w-1 h-12 rounded-full ${eventType.color}`}></div>
                              }
                            />
                          )
                        })}
                      {events.filter(event => {
                        const eventDate = new Date(event.start)
                        return eventDate.toDateString() === currentDate.toDateString()
                      }).length === 0 && (
                        <p className="text-white/50 text-center py-8">No events scheduled for this day</p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Week View */}
              {view === 'week' && (
                <div>
                  <div className="grid grid-cols-7 gap-2 mb-4">
                    {weekDates.map((date, index) => {
                      const isToday = date.toDateString() === new Date().toDateString()
                      const dayEvents = events.filter(event => {
                        const eventDate = new Date(event.start)
                        return eventDate.toDateString() === date.toDateString()
                      })

                      return (
                        <div key={index} className="text-center">
                          <p className="text-xs text-white/50 mb-2">{days[index]}</p>
                          <div className={`
                            p-3 rounded-xl transition-all cursor-pointer
                            ${isToday
                              ? 'bg-purple-600 text-white font-semibold shadow-lg'
                              : 'bg-white/5 hover:bg-white/10'}
                          `}>
                            <div className="text-lg mb-1">{date.getDate()}</div>
                            {dayEvents.length > 0 && (
                              <div className="flex justify-center space-x-1">
                                {dayEvents.slice(0, 3).map((_, i) => (
                                  <div key={i} className="w-1 h-1 bg-purple-400 rounded-full"></div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {/* Today's Schedule */}
                  <div className="border-t border-white/10 pt-4">
                    <h3 className="text-lg font-semibold mb-3">Today's Schedule</h3>
                    {loading ? (
                      <div className="space-y-3">
                        {[1, 2, 3].map(i => (
                          <div key={i} className="skeleton h-20"></div>
                        ))}
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {events
                          .filter(event => {
                            const eventDate = new Date(event.start)
                            return eventDate.toDateString() === new Date().toDateString()
                          })
                          .map(event => {
                            const eventType = getEventType(event)
                            return (
                              <ListItem
                                key={event.id}
                                title={event.title}
                                subtitle={`${formatTime(event.start)} - ${formatTime(event.end)}`}
                                icon={eventType.icon}
                                onClick={() => setSelectedEvent(event)}
                                rightElement={
                                  <div className={`w-1 h-12 rounded-full ${eventType.color}`}></div>
                                }
                              />
                            )
                          })}
                        {events.filter(event => {
                          const eventDate = new Date(event.start)
                          return eventDate.toDateString() === new Date().toDateString()
                        }).length === 0 && (
                          <p className="text-white/50 text-center py-8">No events scheduled for today</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Month View */}
              {view === 'month' && (
                <div>
                  <div className="grid grid-cols-7 gap-1 mb-4">
                    {days.map(day => (
                      <div key={day} className="p-2 text-center text-sm font-medium text-white/70">
                        {day}
                      </div>
                    ))}
                    {monthDates.map((date, index) => {
                      const isToday = date.toDateString() === new Date().toDateString()
                      const isCurrentMonth = date.getMonth() === currentDate.getMonth()
                      const dayEvents = events.filter(event => {
                        const eventDate = new Date(event.start)
                        return eventDate.toDateString() === date.toDateString()
                      })

                      return (
                        <div
                          key={index}
                          onClick={() => setCurrentDate(new Date(date))}
                          className={`
                            aspect-square p-1 rounded-lg transition-all cursor-pointer text-center
                            ${isToday
                              ? 'bg-purple-600 text-white font-semibold'
                              : isCurrentMonth
                                ? 'bg-white/5 hover:bg-white/10 text-white'
                                : 'bg-white/2 text-white/30 hover:text-white/50'}
                          `}
                        >
                          <div className="text-sm mb-1">{date.getDate()}</div>
                          {dayEvents.length > 0 && (
                            <div className="flex justify-center space-x-1">
                              {dayEvents.slice(0, 2).map((_, i) => (
                                <div key={i} className="w-1 h-1 bg-purple-400 rounded-full"></div>
                              ))}
                              {dayEvents.length > 2 && (
                                <div className="w-1 h-1 bg-purple-600 rounded-full"></div>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Upcoming Events */}
          <div>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">
                {view === 'day' ? 'Other Events Today' :
                 view === 'week' ? 'This Week' :
                 'Upcoming Events'}
              </h3>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className="skeleton h-16"></div>
                  ))}
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {events
                    .filter(event => {
                      const eventDate = new Date(event.start)
                      const now = new Date()

                      if (view === 'day') {
                        return eventDate.toDateString() === currentDate.toDateString() && eventDate > now
                      } else if (view === 'week') {
                        const weekStart = new Date(currentDate)
                        weekStart.setDate(weekStart.getDate() - weekStart.getDay())
                        const weekEnd = new Date(weekStart)
                        weekEnd.setDate(weekEnd.getDate() + 6)
                        weekEnd.setHours(23, 59, 59, 999)
                        return eventDate >= weekStart && eventDate <= weekEnd
                      } else {
                        return eventDate > now
                      }
                    })
                    .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
                    .slice(0, 10)
                    .map(event => {
                      const eventType = getEventType(event)
                      return (
                        <div
                          key={event.id}
                          onClick={() => setSelectedEvent(event)}
                          className="p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors cursor-pointer"
                        >
                          <div className="flex items-start space-x-3">
                            <span className="text-lg mt-1">{eventType.icon}</span>
                            <div className="flex-1">
                              <p className="font-medium text-sm">{event.title}</p>
                              <p className="text-xs text-white/50 mt-1">
                                {formatDate(event.start)}
                              </p>
                              <p className="text-xs text-white/50">
                                {formatTime(event.start)}
                              </p>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  {events.filter(event => {
                    const eventDate = new Date(event.start)
                    const now = new Date()

                    if (view === 'day') {
                      return eventDate.toDateString() === currentDate.toDateString() && eventDate > now
                    } else if (view === 'week') {
                      const weekStart = new Date(currentDate)
                      weekStart.setDate(weekStart.getDate() - weekStart.getDay())
                      const weekEnd = new Date(weekStart)
                      weekEnd.setDate(weekEnd.getDate() + 6)
                      weekEnd.setHours(23, 59, 59, 999)
                      return eventDate >= weekStart && eventDate <= weekEnd
                    } else {
                      return eventDate > now
                    }
                  }).length === 0 && (
                    <p className="text-white/50 text-center py-8">
                      {view === 'day' ? 'No more events today' :
                       view === 'week' ? 'No events this week' :
                       'No upcoming events'}
                    </p>
                  )}
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>

      {/* Create Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6">Create New Event</h2>

            <div className="space-y-4">
            <div>
                <label className="block text-sm font-medium mb-2">Title *</label>
              <input
                type="text"
                  value={newEvent.summary}
                  onChange={(e) => setNewEvent({ ...newEvent, summary: e.target.value })}
                  className="input"
                placeholder="Event title"
              />
            </div>

              <div>
                <label className="block text-sm font-medium mb-2">Date *</label>
                <input
                  type="date"
                  value={newEvent.date}
                  onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })}
                  className="input"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Start Time *</label>
                  <input
                    type="time"
                    value={newEvent.startTime}
                    onChange={(e) => setNewEvent({ ...newEvent, startTime: e.target.value })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">End Time</label>
                  <input
                    type="time"
                    value={newEvent.endTime}
                    onChange={(e) => setNewEvent({ ...newEvent, endTime: e.target.value })}
                    className="input"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Location</label>
                <input
                  type="text"
                  value={newEvent.location}
                  onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                  className="input"
                  placeholder="Add location"
                />
              </div>

            <div>
                <label className="block text-sm font-medium mb-2">Description</label>
              <textarea
                value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  className="input min-h-[100px]"
                  placeholder="Add description"
              />
            </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={createEvent}
                className="btn-primary"
              >
                Create Event
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-xl font-bold">{selectedEvent.title}</h2>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-white/50 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <span className="text-lg">📅</span>
                <div>
                  <p className="font-medium">
                    {formatDate(selectedEvent.start)}
                  </p>
                  <p className="text-sm text-white/50">
                    {formatTime(selectedEvent.start)} - {formatTime(selectedEvent.end)}
                  </p>
                </div>
              </div>

              {selectedEvent.location && (
                <div className="flex items-center space-x-3">
                  <span className="text-lg">📍</span>
                  <p>{selectedEvent.location}</p>
                </div>
              )}

              {selectedEvent.description && (
                <div className="flex items-start space-x-3">
                  <span className="text-lg">📝</span>
                  <p className="text-sm text-white/70">{selectedEvent.description}</p>
                </div>
              )}

              {selectedEvent.attendees && selectedEvent.attendees.length > 0 && (
                <div className="flex items-start space-x-3">
                  <span className="text-lg">👥</span>
                  <div>
                    <p className="font-medium mb-1">Attendees</p>
                    {selectedEvent.attendees.map((attendee, index) => (
                      <p key={index} className="text-sm text-white/70">
                        {attendee.email}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => deleteEvent(selectedEvent.id)}
                className="btn-ghost text-red-400 hover:text-red-300"
              >
                Delete
              </button>
              <button
                onClick={() => setSelectedEvent(null)}
                className="btn-primary"
              >
                Close
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}