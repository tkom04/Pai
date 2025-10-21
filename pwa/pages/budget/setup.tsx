"use client"
import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'

interface SuggestedCategory {
  key: string
  label: string
  target: number
  is_essential: boolean
  confidence: number
}

interface DebtRecommendation {
  strategy: string
  recommendation: string
  reasoning: string
  avalanche: any
  snowball: any
}

interface BudgetSetupProps {
  isOpen: boolean
  onClose: () => void
  onComplete: () => void
}

const BudgetSetup = ({ isOpen, onClose, onComplete }: BudgetSetupProps) => {
  const router = useRouter()
  const [currentStep, setCurrentStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [suggestedCategories, setSuggestedCategories] = useState<SuggestedCategory[]>([])
  const [debtRecommendations, setDebtRecommendations] = useState<DebtRecommendation | null>(null)
  const [spendingInsights, setSpendingInsights] = useState<string[]>([])
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set())
  const [customAmounts, setCustomAmounts] = useState<Record<string, number>>({})
  const [selectedDebtStrategy, setSelectedDebtStrategy] = useState<string>('')

  const totalSteps = 5

  useEffect(() => {
    if (isOpen && currentStep === 1) {
      analyzeSpendingPatterns()
    }
  }, [isOpen, currentStep])

  const analyzeSpendingPatterns = async () => {
    try {
      setLoading(true)
      const response = await api.post('/api/budget/auto-generate', {}, {
        params: { lookback_days: 90 }
      })

      if (response.data.ok) {
        setSuggestedCategories(response.data.suggested_categories)
        setSpendingInsights(response.data.spending_insights)

        // Select all categories by default
        const allKeys = response.data.suggested_categories.map((cat: SuggestedCategory) => cat.key)
        setSelectedCategories(new Set(allKeys))

        // Set custom amounts to suggested amounts
        const amounts: Record<string, number> = {}
        response.data.suggested_categories.forEach((cat: SuggestedCategory) => {
          amounts[cat.key] = cat.target
        })
        setCustomAmounts(amounts)

        // Load debt recommendations
        if (response.data.debt_recommendations.length > 0) {
          setDebtRecommendations(response.data.debt_recommendations[0])
          setSelectedDebtStrategy(response.data.debt_recommendations[0].strategy)
        }
      }
    } catch (error) {
      showToast(`Failed to analyze spending: ${handleApiError(error)}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryToggle = (categoryKey: string) => {
    const newSelected = new Set(selectedCategories)
    if (newSelected.has(categoryKey)) {
      newSelected.delete(categoryKey)
    } else {
      newSelected.add(categoryKey)
    }
    setSelectedCategories(newSelected)
  }

  const handleAmountChange = (categoryKey: string, amount: number) => {
    setCustomAmounts(prev => ({
      ...prev,
      [categoryKey]: amount
    }))
  }

  const activateBudget = async () => {
    try {
      setLoading(true)

      // Create budget categories
      for (const categoryKey of selectedCategories) {
        const category = suggestedCategories.find(cat => cat.key === categoryKey)
        if (category) {
          await api.post('/api/budget/categories', {
            key: categoryKey,
            label: category.label,
            target: customAmounts[categoryKey] || category.target,
            rollover: false,
            order: suggestedCategories.indexOf(category)
          })
        }
      }

      showToast('Budget activated successfully!', 'success')
      onComplete()
      router.push('/budget')
    } catch (error) {
      showToast(`Failed to activate budget: ${handleApiError(error)}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const getStepTitle = () => {
    switch (currentStep) {
      case 1: return 'Analyzing Your Spending'
      case 2: return 'Suggested Budget Categories'
      case 3: return 'Recurring Payments'
      case 4: return 'Debt Strategy'
      case 5: return 'Review & Activate'
      default: return 'Budget Setup'
    }
  }

  const getStepDescription = () => {
    switch (currentStep) {
      case 1: return 'We\'re analyzing your spending patterns from the last 90 days...'
      case 2: return 'Based on your spending, we\'ve suggested these budget categories:'
      case 3: return 'Review detected recurring payments and subscriptions:'
      case 4: return 'Choose your debt paydown strategy:'
      case 5: return 'Review your budget settings before activating:'
      default: return ''
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg p-6 max-w-4xl w-full mx-4 border border-white/10 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">{getStepTitle()}</h2>
            <p className="text-white/70 text-sm mt-1">{getStepDescription()}</p>
          </div>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Progress Stepper */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep
                    ? 'bg-blue-600 text-white'
                    : 'bg-white/20 text-white/70'
                }`}>
                  {step}
                </div>
                {step < totalSteps && (
                  <div className={`w-16 h-1 mx-2 ${
                    step < currentStep ? 'bg-blue-600' : 'bg-white/20'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="mb-8">
          {/* Step 1: Analyzing */}
          {currentStep === 1 && (
            <div className="text-center py-12">
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <h3 className="text-xl font-semibold text-white mb-2">Analyzing Your Spending</h3>
                  <p className="text-white/70">Fetching transactions from your bank accounts...</p>
                </>
              ) : (
                <>
                  <div className="text-green-400 mb-4">
                    <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">Analysis Complete!</h3>
                  <p className="text-white/70">We've analyzed your spending patterns and generated recommendations.</p>
                </>
              )}
            </div>
          )}

          {/* Step 2: Categories */}
          {currentStep === 2 && (
            <div className="space-y-4">
              {suggestedCategories.map((category) => (
                <div key={category.key} className="border border-white/20 rounded-lg p-4 bg-white/5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={selectedCategories.has(category.key)}
                        onChange={() => handleCategoryToggle(category.key)}
                        className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded"
                      />
                      <div>
                        <h4 className="text-white font-medium">{category.label}</h4>
                        <div className="flex items-center space-x-2 text-sm text-white/70">
                          <span className={`px-2 py-1 rounded text-xs ${
                            category.is_essential ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'
                          }`}>
                            {category.is_essential ? 'Essential' : 'Discretionary'}
                          </span>
                          <span>Confidence: {Math.round(category.confidence * 100)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {selectedCategories.has(category.key) && (
                    <div className="mt-3">
                      <label className="block text-sm font-medium text-white mb-1">
                        Monthly Budget (£)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={customAmounts[category.key] || category.target}
                        onChange={(e) => handleAmountChange(category.key, parseFloat(e.target.value))}
                        className="w-full border border-white/20 rounded-lg px-3 py-2 bg-white/5 text-white"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Step 3: Recurring Payments */}
          {currentStep === 3 && (
            <div className="text-center py-12">
              <div className="text-blue-400 mb-4">
                <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Recurring Payments</h3>
              <p className="text-white/70">We'll detect recurring payments automatically as you use the system.</p>
            </div>
          )}

          {/* Step 4: Debt Strategy */}
          {currentStep === 4 && debtRecommendations && (
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-xl font-semibold text-white mb-2">Choose Your Debt Strategy</h3>
                <p className="text-white/70">Based on your debt accounts, we recommend the {debtRecommendations.strategy} method.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedDebtStrategy === 'avalanche'
                    ? 'border-blue-500 bg-blue-500/20'
                    : 'border-white/20 bg-white/5 hover:bg-white/10'
                }`} onClick={() => setSelectedDebtStrategy('avalanche')}>
                  <h4 className="text-white font-semibold mb-2">Avalanche Method</h4>
                  <p className="text-white/70 text-sm">Pay highest interest debts first. Saves more money overall.</p>
                </div>

                <div className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedDebtStrategy === 'snowball'
                    ? 'border-blue-500 bg-blue-500/20'
                    : 'border-white/20 bg-white/5 hover:bg-white/10'
                }`} onClick={() => setSelectedDebtStrategy('snowball')}>
                  <h4 className="text-white font-semibold mb-2">Snowball Method</h4>
                  <p className="text-white/70 text-sm">Pay smallest balances first. Provides psychological motivation.</p>
                </div>
              </div>

              <div className="p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                <p className="text-blue-400 text-sm">
                  <strong>Recommendation:</strong> {debtRecommendations.reasoning}
                </p>
              </div>
            </div>
          )}

          {/* Step 5: Review */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-semibold text-white mb-4">Budget Summary</h3>

                <div className="space-y-3">
                  <div className="flex justify-between text-white">
                    <span>Selected Categories:</span>
                    <span>{selectedCategories.size}</span>
                  </div>
                  <div className="flex justify-between text-white">
                    <span>Total Monthly Budget:</span>
                    <span>£{Object.entries(customAmounts)
                      .filter(([key]) => selectedCategories.has(key))
                      .reduce((sum, [, amount]) => sum + amount, 0)
                      .toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-white">
                    <span>Debt Strategy:</span>
                    <span className="capitalize">{selectedDebtStrategy}</span>
                  </div>
                </div>
              </div>

              {spendingInsights.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-white mb-3">Spending Insights</h4>
                  <div className="space-y-2">
                    {spendingInsights.map((insight, index) => (
                      <div key={index} className="p-3 bg-white/5 border border-white/20 rounded-lg">
                        <p className="text-white/80 text-sm">{insight}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={prevStep}
            disabled={currentStep === 1}
            className="px-4 py-2 border border-white/20 rounded-lg text-white hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-white/20 rounded-lg text-white hover:bg-white/10 transition-colors"
            >
              Cancel
            </button>

            {currentStep < totalSteps ? (
              <button
                onClick={nextStep}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                Next
              </button>
            ) : (
              <button
                onClick={activateBudget}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Activating...' : 'Activate Budget'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default BudgetSetup
