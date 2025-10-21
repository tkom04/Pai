"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'
import { Card } from '@/components/ui/Card'

interface BudgetCategory {
  id: string
  key: string
  label: string
  target: number
  rollover: boolean
  order: number
}

interface BudgetSettings {
  currency: string
  cycle_start_day: number
  show_ai_overview: boolean
  consent_version?: string
}

const Settings = () => {
  const [categories, setCategories] = useState<BudgetCategory[]>([])
  const [settings, setSettings] = useState<BudgetSettings>({
    currency: 'GBP',
    cycle_start_day: 1,
    show_ai_overview: false
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const [newCategory, setNewCategory] = useState({
    key: '',
    label: '',
    target: '',
    rollover: false
  })

  const [showAddCategory, setShowAddCategory] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [categoriesRes, settingsRes] = await Promise.all([
        api.get('/api/budget/categories'),
        api.get('/api/budget/settings').catch(() => ({ data: settings }))
      ])

      setCategories(categoriesRes.data.categories || [])
      setSettings(settingsRes.data || settings)
    } catch (error) {
      showToast(`Failed to load settings: ${handleApiError(error)}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleAddCategory = async () => {
    if (!newCategory.key || !newCategory.label || !newCategory.target) {
      showToast('Please fill in all required fields', 'error')
      return
    }

    // Optimistic UI update
    const tempId = 'temp-' + Date.now()
    const tempCategory = {
      id: tempId,
      key: newCategory.key,
      label: newCategory.label,
      target: parseFloat(newCategory.target),
      rollover: newCategory.rollover,
      order: categories.length
    }

    setCategories(prev => [...prev, tempCategory])
    setShowAddCategory(false)
    setNewCategory({ key: '', label: '', target: '', rollover: false })

    try {
      const result = await api.post('/api/budget/categories', {
        key: newCategory.key,
        label: newCategory.label,
        target: parseFloat(newCategory.target),
        rollover: newCategory.rollover,
        order: categories.length
      })

      // Replace temp with real
      setCategories(prev => prev.map(c =>
        c.id === tempId ? { ...result.data.category, id: result.data.category.id } : c
      ))
      showToast('Category added successfully', 'success')
    } catch (error) {
      // Rollback on failure
      setCategories(prev => prev.filter(c => c.id !== tempId))
      showToast(`Failed to add category: ${handleApiError(error)}`, 'error')
    }
  }

  const handleDeleteCategory = async (categoryKey: string) => {
    if (!confirm('Are you sure you want to delete this category?')) {
      return
    }

    // Optimistic UI update
    const originalCategories = [...categories]
    setCategories(prev => prev.filter(c => c.key !== categoryKey))

    try {
      await api.delete(`/api/budget/categories/${categoryKey}`)
      showToast('Category deleted successfully', 'success')
    } catch (error) {
      // Rollback on failure
      setCategories(originalCategories)
      showToast(`Failed to delete category: ${handleApiError(error)}`, 'error')
    }
  }

  const handleUpdateCategory = async (categoryKey: string, updates: Partial<BudgetCategory>) => {
    // Optimistic UI update
    const originalCategories = [...categories]
    setCategories(prev => prev.map(c =>
      c.key === categoryKey ? { ...c, ...updates } : c
    ))

    try {
      await api.post('/api/budget/categories', {
        key: categoryKey,
        label: updates.label || '',
        target: updates.target || 0,
        rollover: updates.rollover || false,
        order: updates.order || 0
      })
      showToast('Category updated successfully', 'success')
    } catch (error) {
      // Rollback on failure
      setCategories(originalCategories)
      showToast(`Failed to update category: ${handleApiError(error)}`, 'error')
    }
  }

  const handleSaveSettings = async () => {
    setSaving(true)
    try {
      await api.post('/api/budget/settings', settings)
      showToast('Settings saved successfully', 'success')
    } catch (error) {
      showToast(`Failed to save settings: ${handleApiError(error)}`, 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Budget Categories */}
        <Card>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">Budget Categories</h2>
            <button
              onClick={() => setShowAddCategory(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add Category
            </button>
          </div>

          <div className="space-y-4">
            {categories.map((category) => (
              <div key={category.id} className="border rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Label</label>
                    <input
                      type="text"
                      value={category.label}
                      onChange={(e) => handleUpdateCategory(category.key, { label: e.target.value })}
                      className="w-full border rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Target (£)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={category.target}
                      onChange={(e) => handleUpdateCategory(category.key, { target: parseFloat(e.target.value) })}
                      className="w-full border rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={category.rollover}
                        onChange={(e) => handleUpdateCategory(category.key, { rollover: e.target.checked })}
                        className="mr-2"
                      />
                      <label className="text-sm">Rollover</label>
                    </div>
                    <button
                      onClick={() => handleDeleteCategory(category.key)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Budget Settings */}
        <Card>
          <h2 className="text-xl font-semibold mb-6">Budget Settings</h2>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Currency</label>
              <select
                value={settings.currency}
                onChange={(e) => setSettings({ ...settings, currency: e.target.value })}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="GBP">GBP (£)</option>
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Budget Cycle Start Day</label>
              <input
                type="number"
                min="1"
                max="31"
                value={settings.cycle_start_day}
                onChange={(e) => setSettings({ ...settings, cycle_start_day: parseInt(e.target.value) })}
                className="w-full border rounded-lg px-3 py-2"
              />
              <p className="text-sm text-gray-600 mt-1">
                Day of the month when your budget cycle starts (1-31)
              </p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="ai_overview"
                checked={settings.show_ai_overview}
                onChange={(e) => setSettings({ ...settings, show_ai_overview: e.target.checked })}
                className="mr-2"
              />
              <label htmlFor="ai_overview" className="text-sm">
                Show AI-powered budget insights
              </label>
            </div>

            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </Card>
      </div>

      {/* Add Category Modal */}
      {showAddCategory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Add Budget Category</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Key (lowercase, underscores)</label>
                <input
                  type="text"
                  value={newCategory.key}
                  onChange={(e) => setNewCategory({ ...newCategory, key: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="e.g., groceries, transport"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Label</label>
                <input
                  type="text"
                  value={newCategory.label}
                  onChange={(e) => setNewCategory({ ...newCategory, label: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="e.g., Groceries & Food"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Target Amount (£)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newCategory.target}
                  onChange={(e) => setNewCategory({ ...newCategory, target: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="0.00"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="rollover"
                  checked={newCategory.rollover}
                  onChange={(e) => setNewCategory({ ...newCategory, rollover: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="rollover" className="text-sm">Enable rollover</label>
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowAddCategory(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddCategory}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add Category
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Settings