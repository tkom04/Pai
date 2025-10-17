import Layout from '@/components/Layout'
import ShoppingList from '@/components/ShoppingList'

export default function ShoppingPage() {
  return (
    <Layout>
      <div className="h-full overflow-y-auto bg-gradient-to-br from-black via-green-900/10 to-black">
        <ShoppingList />
      </div>
    </Layout>
  )
}

