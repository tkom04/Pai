"use client"
import { useState, useEffect } from 'react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

interface ShoppingItem {
  id: string
  item: string
  quantity: number
  category: string
  budget_category: string
  status: 'pending' | 'purchased'
  added_by: string | null
  created_at: string
}

interface NewItem {
  item: string
  quantity: number
  category: string
}

export default function ShoppingList() {
  const [items, setItems] = useState<ShoppingItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newItem, setNewItem] = useState<NewItem>({
    item: '',
    quantity: 1,
    category: 'groceries'
  })
  const [isAdding, setIsAdding] = useState(false)
  const supabase = createClientComponentClient()

  // Fetch shopping list items
  const fetchItems = async () => {
    try {
      setLoading(true)
      setError(null)

      const { data, error } = await supabase
        .from('shopping_list')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error

      setItems(data || [])
    } catch (err) {
      console.error('Error fetching shopping list:', err)
      setError('Failed to load shopping list')
    } finally {
      setLoading(false)
    }
  }

  // Add new item
  const addItem = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newItem.item.trim()) return

    try {
      setIsAdding(true)
      setError(null)

      // Optimistic update
      const tempId = `temp-${Date.now()}`
      const optimisticItem: ShoppingItem = {
        id: tempId,
        item: newItem.item.trim(),
        quantity: newItem.quantity,
        category: newItem.category,
        budget_category: 'groceries',
        status: 'pending',
        added_by: null,
        created_at: new Date().toISOString()
      }

      setItems(prev => [optimisticItem, ...prev])

      const { data, error } = await supabase
        .from('shopping_list')
        .insert([{
          item: newItem.item.trim(),
          quantity: newItem.quantity,
          category: newItem.category,
          budget_category: 'groceries',
          status: 'pending'
        }])
        .select()
        .single()

      if (error) throw error

      // Replace optimistic item with real item
      setItems(prev => prev.map(item =>
        item.id === tempId ? data : item
      ))

      // Reset form
      setNewItem({ item: '', quantity: 1, category: 'groceries' })
    } catch (err) {
      console.error('Error adding item:', err)
      setError('Failed to add item')
      // Remove optimistic item on error
      setItems(prev => prev.filter(item => !item.id.startsWith('temp-')))
    } finally {
      setIsAdding(false)
    }
  }

  // Toggle item status
  const toggleStatus = async (id: string, currentStatus: string) => {
    const newStatus = currentStatus === 'purchased' ? 'pending' : 'purchased'

    try {
      // Optimistic update
      setItems(prev => prev.map(item =>
        item.id === id
          ? { ...item, status: newStatus as 'pending' | 'purchased' }
          : item
      ))

      const { error } = await supabase
        .from('shopping_list')
        .update({
          status: newStatus
        })
        .eq('id', id)

      if (error) throw error
    } catch (err) {
      console.error('Error toggling status:', err)
      setError('Failed to update item')
      // Revert optimistic update
      setItems(prev => prev.map(item =>
        item.id === id
          ? { ...item, status: currentStatus as 'pending' | 'purchased' }
          : item
      ))
    }
  }

  // Delete item
  const deleteItem = async (id: string) => {
    const itemToDelete = items.find(item => item.id === id)

    try {
      // Optimistic update
      setItems(prev => prev.filter(item => item.id !== id))

      const { error } = await supabase
        .from('shopping_list')
        .delete()
        .eq('id', id)

      if (error) throw error
    } catch (err) {
      console.error('Error deleting item:', err)
      setError('Failed to delete item')
      // Revert optimistic update
      if (itemToDelete) {
        setItems(prev => [...prev, itemToDelete].sort((a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ))
      }
    }
  }

  // Set up real-time subscription
  useEffect(() => {
    fetchItems()

    // Subscribe to real-time changes
    const channel = supabase
      .channel('shopping_list_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'shopping_list'
        },
        (payload) => {
          console.log('Real-time update:', payload)

          switch (payload.eventType) {
            case 'INSERT':
              const newItem = payload.new as ShoppingItem
              setItems(prev => {
                // Avoid duplicates (in case of optimistic updates)
                if (prev.some(item => item.id === newItem.id)) {
                  return prev
                }
                return [newItem, ...prev]
              })
              break

            case 'UPDATE':
              const updatedItem = payload.new as ShoppingItem
              setItems(prev => prev.map(item =>
                item.id === updatedItem.id ? updatedItem : item
              ))
              break

            case 'DELETE':
              const deletedItem = payload.old as ShoppingItem
              setItems(prev => prev.filter(item => item.id !== deletedItem.id))
              break
          }
        }
      )
      .subscribe()

    // Cleanup subscription
    return () => {
      supabase.removeChannel(channel)
    }
  }, [supabase])

  // Category options
  const categories = [
    'groceries',
    'household',
    'electronics',
    'clothing',
    'health',
    'other'
  ]

  // Category icons
  const categoryIcons: Record<string, string> = {
    groceries: '🛒',
    household: '🏠',
    electronics: '📱',
    clothing: '👕',
    health: '💊',
    other: '📦'
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6">
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            🛍️ Shopping List
          </h2>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="animate-pulse bg-white/10 rounded-lg h-16"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold flex items-center">
            🛍️ Shopping List
          </h2>
          <div className="text-sm text-white/60">
            {items.length} items • {items.filter(item => item.status === 'purchased').length} purchased
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-200 text-sm">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 text-red-300 hover:text-red-100"
            >
              ✕
            </button>
          </div>
        )}

        {/* Add Item Form */}
        <form onSubmit={addItem} className="mb-6 p-4 bg-white/5 rounded-xl">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <input
                type="text"
                value={newItem.item}
                onChange={(e) => setNewItem(prev => ({ ...prev, item: e.target.value }))}
                placeholder="Item name..."
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isAdding}
              />
            </div>

            <div className="w-24">
              <input
                type="number"
                min="1"
                value={newItem.quantity}
                onChange={(e) => setNewItem(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isAdding}
              />
            </div>

            <div className="w-36">
              <select
                value={newItem.category}
                onChange={(e) => setNewItem(prev => ({ ...prev, category: e.target.value }))}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={isAdding}
              >
                {categories.map(category => (
                  <option key={category} value={category} className="bg-gray-800">
                    {categoryIcons[category]} {category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={isAdding || !newItem.item.trim()}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-600/50 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
            >
              {isAdding ? '...' : 'Add'}
            </button>
          </div>
        </form>

        {/* Shopping List */}
        <div className="space-y-3">
          {items.length === 0 ? (
            <div className="text-center py-12 text-white/50">
              <div className="text-4xl mb-4">🛒</div>
              <p>Your shopping list is empty</p>
              <p className="text-sm mt-2">Add items above to get started</p>
            </div>
          ) : (
            items.map(item => (
              <div
                key={item.id}
                className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                  item.status === 'purchased'
                    ? 'bg-green-500/10 border-green-500/30 opacity-75'
                    : 'bg-white/5 border-white/10 hover:bg-white/10'
                }`}
              >
                {/* Status Toggle */}
                <button
                  onClick={() => toggleStatus(item.id, item.status)}
                  className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                    item.status === 'purchased'
                      ? 'bg-green-500 border-green-500 text-white'
                      : 'border-white/30 hover:border-white/50'
                  }`}
                >
                  {item.status === 'purchased' && '✓'}
                </button>

                {/* Category Icon */}
                <div className="text-xl">
                  {categoryIcons[item.category] || categoryIcons.other}
                </div>

                {/* Item Details */}
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className={`font-medium ${
                      item.status === 'purchased' ? 'line-through text-white/60' : 'text-white'
                    }`}>
                      {item.item}
                    </h3>
                    <span className="text-sm text-white/50">
                      × {item.quantity}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-white/40 capitalize">
                      {item.category}
                    </span>
                    <span className="text-xs text-white/30">
                      {new Date(item.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {/* Status Badge */}
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                  item.status === 'purchased'
                    ? 'bg-green-500/20 text-green-300'
                    : 'bg-orange-500/20 text-orange-300'
                }`}>
                  {item.status === 'purchased' ? 'Purchased' : 'Pending'}
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => deleteItem(item.id)}
                  className="w-8 h-8 flex items-center justify-center text-white/40 hover:text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                  title="Delete item"
                >
                  🗑️
                </button>
              </div>
            ))
          )}
        </div>

        {/* Summary */}
        {items.length > 0 && (
          <div className="mt-6 pt-4 border-t border-white/10">
            <div className="flex justify-between text-sm text-white/60">
              <span>
                {items.filter(item => item.status === 'pending').length} items remaining
              </span>
              <span>
                {Math.round((items.filter(item => item.status === 'purchased').length / items.length) * 100)}% complete
              </span>
            </div>
            <div className="mt-2 w-full bg-white/10 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${(items.filter(item => item.status === 'purchased').length / items.length) * 100}%`
                }}
              ></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
