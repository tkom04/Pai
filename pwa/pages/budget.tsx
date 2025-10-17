import Layout from '@/components/Layout'
import BudgetView from '@/components/BudgetView'

export default function BudgetPage() {
  return (
    <Layout>
      <div className="h-full overflow-y-auto bg-gradient-to-br from-black via-purple-900/10 to-black">
        <BudgetView />
      </div>
    </Layout>
  )
}

