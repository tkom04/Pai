import Layout from '@/components/Layout'
import TasksView from '@/components/TasksView'

export default function TasksPage() {
  return (
    <Layout>
      <div className="h-full overflow-y-auto bg-gradient-to-br from-black via-blue-900/10 to-black">
        <TasksView />
      </div>
    </Layout>
  )
}

