"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'

interface GoogleCalendarEvent {
  id: string
  title: string
  start: string
  end: string
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

      // IMPORTANT: Backend expects 'start' and 'end', not 'start_date' and 'end_date'
      const response = await api.get('/events', {
        params: {
          start: startOfDay.toISOString(),
          end: endOfDay.toISOString()
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

      setTodayEventCount(todayEvents.length)
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

export default MiniCalendarWidget

