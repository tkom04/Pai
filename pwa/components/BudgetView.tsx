"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'
import { Card, StatCard } from './ui/Card'
import BankConnectionCard from './BankConnectionCard'
import DuplicateDetection from './DuplicateDetection'
import BudgetSetup from '../pages/budget/setup'

interface BudgetCategory {
  key: string
  label: string
  target: number
  spent: number
  remaining: number
  rollover: boolean
}

interface BudgetSummary {
  period: string
  last_updated: string
  totals: {
    spent: number
    income: number
    savings: number
  }
  categories: BudgetCategory[]
  coverage_pct: number
}

interface BankConnection {
  id: string
  institution_id: string
  institution_name: string
  institution_display_name: string
  institution_logo: string
  status: 'active' | 'expired' | 'revoked'
  created_at: string
  last_sync: string
  days_until_expiry: number | null
}

const BudgetView = () => {
  const [budgetData, setBudgetData] = useState<BudgetSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [selectedPeriod, setSelectedPeriod] = useState<string>('')
  const [showCreateCategoryModal, setShowCreateCategoryModal] = useState(false)
  const [showCreateRuleModal, setShowCreateRuleModal] = useState(false)
  const [bankConnected, setBankConnected] = useState(false)
  const [checkingBankStatus, setCheckingBankStatus] = useState(true)
  const [bankConnections, setBankConnections] = useState<BankConnection[]>([])
  const [loadingConnections, setLoadingConnections] = useState(false)
  const [showBankManagement, setShowBankManagement] = useState(false)
  const [showDuplicateDetection, setShowDuplicateDetection] = useState(false)
  const [showBudgetSetup, setShowBudgetSetup] = useState(false)

  const [newCategory, setNewCategory] = useState({
    key: '',
    label: '',
    target: '',
    rollover: false,
    order: 0
  })

  const [newRule, setNewRule] = useState({
    priority: 100,
    matchers: {} as Record<string, any>,
    category_key: ''
  })

  // Initialize period
  useEffect(() => {
    const now = new Date()
    const currentPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    setSelectedPeriod(currentPeriod)
  }, [])

  // Check bank connection status
  useEffect(() => {
    checkBankStatus()

    // Check for bank auth success/error messages in URL
    const urlParams = new URLSearchParams(window.location.search)
    const authStatus = urlParams.get('auth')
    const error = urlParams.get('error')

    if (authStatus === 'success') {
      showToast('Bank account connected successfully!', 'success')
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
      // Refresh bank status
      checkBankStatus()
    } else if (authStatus === 'error') {
      showToast(`Bank connection failed: ${error || 'Unknown error'}`, 'error')
      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname)
    }
  }, [])

  // Load budget data when period changes
  useEffect(() => {
    if (selectedPeriod) {
      loadBudgetSummary()
    }
  }, [selectedPeriod])

  const checkBankStatus = async () => {
    try {
      setCheckingBankStatus(true)
      const response = await api.get('/auth/open-banking/status')
      setBankConnected(response.data.authenticated)

      // Also load bank connections if authenticated
      if (response.data.authenticated) {
        await loadBankConnections()
      }
    } catch (error) {
      console.error('Failed to check bank status:', error)
      setBankConnected(false)
    } finally {
      setCheckingBankStatus(false)
    }
  }

  const loadBankConnections = async () => {
    try {
      setLoadingConnections(true)
      const response = await api.get('/api/banking/connections')
      if (response.data.ok) {
        setBankConnections(response.data.connections)
      }
    } catch (error) {
      console.error('Failed to load bank connections:', error)
      showToast('Failed to load bank connections', 'error')
    } finally {
      setLoadingConnections(false)
    }
  }

  const handleRevokeConnection = (connectionId: string) => {
    setBankConnections(prev => prev.filter(conn => conn.id !== connectionId))

    // Check if any connections remain
    const remainingConnections = bankConnections.filter(conn => conn.id !== connectionId)
    if (remainingConnections.length === 0) {
      setBankConnected(false)
    }
  }

  const handleSyncConnection = (connectionId: string) => {
    // Update last sync time for the connection
    setBankConnections(prev => prev.map(conn =>
      conn.id === connectionId
        ? { ...conn, last_sync: new Date().toISOString() }
        : conn
    ))
  }

  const handleConnectBank = async () => {
    try {
      const response = await api.get('/auth/open-banking')
      window.location.href = response.data.authorization_url
    } catch (error) {
      showToast('Failed to connect bank', 'error')
    }
  }

  const handleRefresh = async () => {
    setLoading(true)
    try {
      const result = await api.post('/api/budget/refresh', {}, {
        params: { lookback_days: 90 }
      })

      // Handle warnings
      if (result.data.warnings) {
        result.data.warnings.forEach((w: any) => {
          showToast(w.message, 'warning')
        })
      }

      setLastUpdated(new Date(result.data.last_updated).toLocaleString())

      // Fetch summary
      const summary = await api.get('/api/budget/summary', {
        params: { period: selectedPeriod }
      })
      setBudgetData(summary.data)

      showToast(`✓ Refreshed ${result.data.transactions_count} transactions (${(result.data.coverage * 100).toFixed(0)}% categorized)`, 'success')
    } catch (error: any) {
      if (error.response?.status === 409) {
        showToast('Refresh already in progress', 'info')
      } else if (error.response?.status === 401) {
        showToast('Session expired. Please reconnect your bank', 'error')
        // Redirect to connect flow
        window.location.href = '/budget?connect=true'
      } else {
        showToast(`Failed to refresh: ${handleApiError(error)}`, 'error')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadBudgetSummary = async () => {
    try {
      const response = await api.get('/api/budget/summary', {
        params: { period: selectedPeriod }
      })
      setBudgetData(response.data)
    } catch (error: any) {
      if (error.response?.status === 422) {
        // No data available, show helpful message
        const message = error.response?.data?.message || 'No budget data available'
        showToast(message, 'info')
        setBudgetData(null)
      } else if (error.response?.status === 401) {
        // Not authenticated, redirect to bank connection
        showToast('Please connect your bank first', 'warning')
        setBankConnected(false)
      } else {
        showToast(`Failed to load budget: ${handleApiError(error)}`, 'error')
        setBudgetData(null)
      }
    }
  }


  const handleCreateCategory = async () => {
    try {
      const categoryData = {
        ...newCategory,
        target: parseFloat(newCategory.target),
        order: budgetData?.categories.length || 0
      }

      await api.post('/api/budget/categories', categoryData)
      setShowCreateCategoryModal(false)
      setNewCategory({ key: '', label: '', target: '', rollover: false, order: 0 })
      showToast('Category created successfully', 'success')
      loadBudgetSummary()
    } catch (error) {
      showToast(`Failed to create category: ${handleApiError(error)}`, 'error')
    }
  }

  const handleCreateRule = async () => {
    try {
      await api.post('/api/budget/rules', newRule)
      setShowCreateRuleModal(false)
      setNewRule({ priority: 100, matchers: {}, category_key: '' })
      showToast('Rule created successfully', 'success')
    } catch (error) {
      showToast(`Failed to create rule: ${handleApiError(error)}`, 'error')
    }
  }

  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period)
  }

  const generatePeriodOptions = () => {
    const options = []
    const now = new Date()

    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      const label = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
      options.push({ value: period, label })
    }

    return options
  }

  if (checkingBankStatus) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!bankConnected) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto text-center">
          <Card className="bg-white/5 border-white/10">
            <h1 className="text-3xl font-bold mb-4 text-white">Budget Management</h1>
            <p className="text-white/70 mb-8">
              Connect your bank account to start tracking your spending and managing your budget.
            </p>
            <button
              onClick={handleConnectBank}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Connect Bank Account
            </button>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">Budget Overview</h1>
          {lastUpdated && (
            <p className="text-white/70 text-sm mt-1">
              Last updated: {lastUpdated}
            </p>
          )}
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => setShowBankManagement(!showBankManagement)}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
          >
            {showBankManagement ? 'Hide Banks' : 'Manage Banks'}
          </button>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            onClick={() => setShowCreateCategoryModal(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Add Category
          </button>
          <button
            onClick={() => setShowCreateRuleModal(true)}
            className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
          >
            Add Rule
          </button>
          <button
            onClick={() => setShowDuplicateDetection(true)}
            className="bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors"
          >
            Check Duplicates
          </button>
          <button
            onClick={() => setShowBudgetSetup(true)}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
          >
            AI Setup
          </button>
        </div>
      </div>

      {/* Period Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2 text-white">Period</label>
        <select
          value={selectedPeriod}
          onChange={(e) => handlePeriodChange(e.target.value)}
          className="border border-white/20 rounded-lg px-3 py-2 bg-white/5 text-white"
        >
          {generatePeriodOptions().map(option => (
            <option key={option.value} value={option.value} className="bg-gray-800 text-white">
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Bank Management Section */}
      {showBankManagement && (
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">Bank Connections</h2>
            <button
              onClick={handleConnectBank}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <span>+</span>
              <span>Add Bank</span>
            </button>
          </div>

          {loadingConnections ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2 text-white">Loading connections...</span>
            </div>
          ) : bankConnections.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {bankConnections.map((connection) => (
                <BankConnectionCard
                  key={connection.id}
                  connection={connection}
                  onRevoke={handleRevokeConnection}
                  onSync={handleSyncConnection}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-white/70 mb-4">
                <svg className="mx-auto h-12 w-12 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-white mb-2">No bank connections</h3>
              <p className="text-white/70 mb-4">Connect your bank accounts to start tracking your spending</p>
              <button
                onClick={handleConnectBank}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Connect Your First Bank
              </button>
            </div>
          )}
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 max-w-sm w-full mx-4 border border-white/10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <h3 className="text-lg font-semibold mb-2 text-white">Refreshing Budget Data</h3>
              <p className="text-white/70 text-sm">
                Fetching transactions from your bank accounts...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Budget Summary */}
      {budgetData && (
        <>
          {/* Totals */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <StatCard
              title="Total Spent"
              value={`£${budgetData.totals.spent.toFixed(2)}`}
              color="red"
            />
            <StatCard
              title="Total Income"
              value={`£${budgetData.totals.income.toFixed(2)}`}
              color="green"
            />
            <StatCard
              title="Categorization"
              value={`${(budgetData.coverage_pct * 100).toFixed(0)}%`}
              color="blue"
            />
          </div>

          {/* Categories */}
          <Card className="bg-white/5 border-white/10">
            <h2 className="text-xl font-semibold mb-4 text-white">Budget Categories</h2>
            <div className="space-y-4">
              {budgetData.categories.map((category) => (
                <div key={category.key} className="border border-white/20 rounded-lg p-4 bg-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="font-medium text-white">{category.label}</h3>
                    <span className="text-sm text-white/70">
                      £{category.spent.toFixed(2)} / £{category.target.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        category.spent > category.target ? 'bg-red-500' : 'bg-blue-500'
                      }`}
                      style={{
                        width: `${Math.min((category.spent / category.target) * 100, 100)}%`
                      }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span className={category.remaining < 0 ? 'text-red-600' : 'text-green-600'}>
                      {category.remaining < 0 ? 'Over budget' : `£${category.remaining.toFixed(2)} remaining`}
                    </span>
                    {category.rollover && (
                      <span className="text-blue-600">Rollover enabled</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}

      {/* Create Category Modal */}
      {showCreateCategoryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Create Budget Category</h3>
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
                onClick={() => setShowCreateCategoryModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCategory}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Rule Modal */}
      {showCreateRuleModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Create Budget Rule</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Category</label>
                <select
                  value={newRule.category_key}
                  onChange={(e) => setNewRule({ ...newRule, category_key: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">Select category</option>
                  {budgetData?.categories.map((cat) => (
                    <option key={cat.key} value={cat.key}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Priority (0-1000)</label>
                <input
                  type="number"
                  min="0"
                  max="1000"
                  value={newRule.priority}
                  onChange={(e) => setNewRule({ ...newRule, priority: parseInt(e.target.value) })}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Merchant Name</label>
                <input
                  type="text"
                  value={newRule.matchers.merchant || ''}
                  onChange={(e) => setNewRule({
                    ...newRule,
                    matchers: { ...newRule.matchers, merchant: e.target.value }
                  })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="e.g., Tesco"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description Contains</label>
                <input
                  type="text"
                  value={newRule.matchers.description_contains || ''}
                  onChange={(e) => setNewRule({
                    ...newRule,
                    matchers: { ...newRule.matchers, description_contains: e.target.value }
                  })}
                  className="w-full border rounded-lg px-3 py-2"
                  placeholder="e.g., coffee"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateRuleModal(false)}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateRule}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Duplicate Detection Modal */}
      <DuplicateDetection
        isOpen={showDuplicateDetection}
        onClose={() => setShowDuplicateDetection(false)}
        onConfirm={(txHash, isDuplicate) => {
          console.log(`Transaction ${txHash} marked as ${isDuplicate ? 'duplicate' : 'not duplicate'}`)
        }}
      />

      {/* Budget Setup Wizard */}
      <BudgetSetup
        isOpen={showBudgetSetup}
        onClose={() => setShowBudgetSetup(false)}
        onComplete={() => {
          setShowBudgetSetup(false)
          loadBudgetSummary() // Refresh budget data
        }}
      />
    </div>
  )
}

export default BudgetView