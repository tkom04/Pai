import Layout from '@/components/Layout'
import CalendarView from '@/components/CalendarView'

export default function CalendarPage() {
  return (
    <Layout>
      <div className="h-full overflow-y-auto bg-gradient-to-br from-black via-purple-900/10 to-black">
        <CalendarView />
      </div>
    </Layout>
  )
}

