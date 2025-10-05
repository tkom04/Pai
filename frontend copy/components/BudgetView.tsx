"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'
import { Card, StatCard } from './ui/Card'

interface Budget {
  id: string
  name: string
  amount: number
  spent: number
  category: string
  period: 'monthly' | 'weekly' | 'yearly'
  start_date: string
  end_date: string
}

interface Transaction {
  id: string
  description: string
  amount: number
  category: string
  date: string
  type: 'income' | 'expense'
}

const BudgetView = () => {
  const [budgets, setBudgets] = useState<Budget[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateBudgetModal, setShowCreateBudgetModal] = useState(false)
  const [showAddTransactionModal, setShowAddTransactionModal] = useState(false)
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'year'>('month')

  const [newBudget, setNewBudget] = useState({
    name: '',
    amount: '',
    category: '',
    period: 'monthly' as 'monthly' | 'weekly' | 'yearly'
  })

  const [newTransaction, setNewTransaction] = useState({
    description: '',
    amount: '',
    category: '',
    type: 'expense' as 'income' | 'expense'
  })

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [budgetsRes, transactionsRes] = await Promise.all([
        api.get('/budget_scan'),
        api.get('/events')
      ])
      setBudgets(budgetsRes.data.budgets || [])
      setTransactions(transactionsRes.data.transactions || [])
    } catch (error) {
      showToast(`Failed to fetch budget data: ${handleApiError(error)}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const createBudget = async () => {
    if (!newBudget.name || !newBudget.amount || !newBudget.category) {
      showToast('Please fill in all fields', 'error')
      return
    }

    try {
      await api.post('/budget_scan', {
        period: newBudget.period,
        source: 'manual',
        path: newBudget.name
      })
      showToast('Budget created successfully', 'success')
      setShowCreateBudgetModal(false)
      setNewBudget({
        name: '',
        amount: '',
        category: '',
        period: 'monthly'
      })
      fetchData()
    } catch (error) {
      showToast(`Failed to create budget: ${handleApiError(error)}`, 'error')
    }
  }

  const addTransaction = async () => {
    if (!newTransaction.description || !newTransaction.amount || !newTransaction.category) {
      showToast('Please fill in all fields', 'error')
      return
    }

    try {
      await api.post('/create_event', {
        title: newTransaction.description,
        start: new Date().toISOString(),
        end: new Date().toISOString(),
        description: `Amount: ${newTransaction.amount}, Category: ${newTransaction.category}`
      })
      showToast('Transaction added successfully', 'success')
      setShowAddTransactionModal(false)
      setNewTransaction({
        description: '',
        amount: '',
        category: '',
        type: 'expense'
      })
      fetchData()
    } catch (error) {
      showToast(`Failed to add transaction: ${handleApiError(error)}`, 'error')
    }
  }

  // Calculate totals
  const totalIncome = transactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0)

  const totalExpenses = transactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0)

  const balance = totalIncome - totalExpenses

  const totalBudget = budgets.reduce((sum, b) => sum + b.amount, 0)
  const totalSpent = budgets.reduce((sum, b) => sum + b.spent, 0)
  const remainingBudget = totalBudget - totalSpent

  // Get spending by category
  const spendingByCategory = transactions
    .filter(t => t.type === 'expense')
    .reduce((acc, t) => {
      acc[t.category] = (acc[t.category] || 0) + t.amount
      return acc
    }, {} as Record<string, number>)

  const categories = Object.keys(spendingByCategory).sort((a, b) =>
    spendingByCategory[b] - spendingByCategory[a]
  )

  // Mock chart data (you can integrate a real chart library)
  const getChartHeight = (value: number, max: number) => {
    return Math.max(10, (value / max) * 100)
  }

  const maxSpending = Math.max(...Object.values(spendingByCategory))

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Budget</h1>
            <p className="text-white/50">Track your finances and spending</p>
          </div>
          <div className="flex items-center space-x-3 mt-4 md:mt-0">
            <button
              onClick={() => setShowAddTransactionModal(true)}
              className="btn-secondary"
            >
              + Transaction
            </button>
            <button
              onClick={() => setShowCreateBudgetModal(true)}
              className="btn-primary"
            >
              + Budget
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Balance"
            value={`$${balance.toLocaleString()}`}
            icon="💰"
            trend={balance > 0 ? 'up' : 'down'}
            trendValue={`${Math.abs(balance).toFixed(0)} this month`}
          />
          <StatCard
            title="Income"
            value={`$${totalIncome.toLocaleString()}`}
            icon="📈"
            trend="up"
            trendValue="+12% from last month"
          />
          <StatCard
            title="Expenses"
            value={`$${totalExpenses.toLocaleString()}`}
            icon="📉"
            trend="down"
            trendValue="-5% from last month"
          />
          <StatCard
            title="Remaining Budget"
            value={`$${remainingBudget.toLocaleString()}`}
            subtitle={`of $${totalBudget.toLocaleString()}`}
            icon="🎯"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Spending by Category */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-6">Spending by Category</h3>

              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3, 4].map(i => (
                    <div key={i} className="skeleton h-16"></div>
                  ))}
                </div>
              ) : categories.length > 0 ? (
                <div className="space-y-4">
                  {categories.slice(0, 6).map(category => {
                    const amount = spendingByCategory[category]
                    const percentage = (amount / totalExpenses) * 100

                    return (
                      <div key={category} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-medium capitalize">{category}</span>
                          <span className="text-sm text-white/70">
                            ${amount.toFixed(2)} ({percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-purple-600 rounded-full transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-white/50 text-center py-8">No spending data available</p>
              )}
            </Card>
          </div>

          {/* Budget Overview */}
          <div>
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Budget Overview</h3>

              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="skeleton h-20"></div>
                  ))}
                </div>
              ) : budgets.length > 0 ? (
                <div className="space-y-3">
                  {budgets.map(budget => {
                    const percentage = (budget.spent / budget.amount) * 100
                    const isOverBudget = percentage > 100

                    return (
                      <div
                        key={budget.id}
                        className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">{budget.name}</h4>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            isOverBudget ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                          }`}>
                            {percentage.toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm text-white/70 mb-2">
                          <span>${budget.spent.toFixed(2)}</span>
                          <span>${budget.amount.toFixed(2)}</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              isOverBudget ? 'bg-red-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <p className="text-white/50 text-center py-8">No budgets created</p>
              )}
            </Card>
          </div>
        </div>

        {/* Recent Transactions */}
        <Card className="p-6 mt-6">
          <h3 className="text-lg font-semibold mb-4">Recent Transactions</h3>

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="skeleton h-16"></div>
              ))}
            </div>
          ) : transactions.length > 0 ? (
            <div className="space-y-3">
              {transactions.slice(0, 10).map(transaction => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      transaction.type === 'income' ? 'bg-green-500/20' : 'bg-red-500/20'
                    }`}>
                      <span className="text-lg">
                        {transaction.type === 'income' ? '📈' : '📉'}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">{transaction.description}</p>
                      <p className="text-sm text-white/50">
                        {new Date(transaction.date).toLocaleDateString()} • {transaction.category}
                      </p>
                    </div>
                  </div>
                  <p className={`font-semibold ${
                    transaction.type === 'income' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {transaction.type === 'income' ? '+' : '-'}${transaction.amount.toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-white/50 text-center py-8">No transactions yet</p>
          )}
        </Card>
      </div>

      {/* Create Budget Modal */}
      {showCreateBudgetModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6">
            <h2 className="text-2xl font-bold mb-6">Create New Budget</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Name *</label>
                <input
                  type="text"
                  value={newBudget.name}
                  onChange={(e) => setNewBudget({ ...newBudget, name: e.target.value })}
                  className="input"
                  placeholder="Budget name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Amount *</label>
                <input
                  type="number"
                  value={newBudget.amount}
                  onChange={(e) => setNewBudget({ ...newBudget, amount: e.target.value })}
                  className="input"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Category *</label>
                <input
                  type="text"
                  value={newBudget.category}
                  onChange={(e) => setNewBudget({ ...newBudget, category: e.target.value })}
                  className="input"
                  placeholder="e.g., Food, Transportation"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Period</label>
                <select
                  value={newBudget.period}
                  onChange={(e) => setNewBudget({ ...newBudget, period: e.target.value as 'weekly' | 'monthly' | 'yearly' })}
                  className="input"
                >
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateBudgetModal(false)}
                className="btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={createBudget}
                className="btn-primary"
              >
                Create Budget
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* Add Transaction Modal */}
      {showAddTransactionModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6">
            <h2 className="text-2xl font-bold mb-6">Add Transaction</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Type</label>
                <div className="flex space-x-3">
                  <button
                    onClick={() => setNewTransaction({ ...newTransaction, type: 'expense' })}
                    className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
                      newTransaction.type === 'expense'
                        ? 'bg-red-500 text-white'
                        : 'bg-white/10 text-white/70'
                    }`}
                  >
                    Expense
                  </button>
                  <button
                    onClick={() => setNewTransaction({ ...newTransaction, type: 'income' })}
                    className={`flex-1 py-2 rounded-lg font-medium transition-colors ${
                      newTransaction.type === 'income'
                        ? 'bg-green-500 text-white'
                        : 'bg-white/10 text-white/70'
                    }`}
                  >
                    Income
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description *</label>
                <input
                  type="text"
                  value={newTransaction.description}
                  onChange={(e) => setNewTransaction({ ...newTransaction, description: e.target.value })}
                  className="input"
                  placeholder="Transaction description"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Amount *</label>
                <input
                  type="number"
                  value={newTransaction.amount}
                  onChange={(e) => setNewTransaction({ ...newTransaction, amount: e.target.value })}
                  className="input"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Category *</label>
                <input
                  type="text"
                  value={newTransaction.category}
                  onChange={(e) => setNewTransaction({ ...newTransaction, category: e.target.value })}
                  className="input"
                  placeholder="e.g., Food, Salary"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddTransactionModal(false)}
                className="btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={addTransaction}
                className="btn-primary"
              >
                Add Transaction
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

export default BudgetView