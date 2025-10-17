import Layout from '@/components/Layout'
import WeatherWidget from '@/components/WeatherWidget'
import UpcomingEventsWidget from '@/components/widgets/UpcomingEventsWidget'
import MiniCalendarWidget from '@/components/widgets/MiniCalendarWidget'

export default function DashboardPage() {
  return (
    <Layout>
      <div className="p-6 h-full overflow-y-auto bg-gradient-to-br from-black via-purple-900/5 to-black">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Welcome back!</h1>
            <p className="text-white/50">Here's what's happening today</p>
          </div>

          {/* Widget Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Weather Widget */}
            <div className="lg:col-span-1">
              <WeatherWidget />
            </div>

            {/* Upcoming Events */}
            <div className="lg:col-span-1">
              <UpcomingEventsWidget />
            </div>

            {/* 7 Day Calendar */}
            <div className="lg:col-span-1">
              <MiniCalendarWidget />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
