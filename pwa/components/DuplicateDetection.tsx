"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'

interface DuplicateTransaction {
  id: string
  tx1_hash: string
  tx2_hash: string
  similarity_score: number
  is_duplicate: boolean
  user_confirmed: boolean
  created_at: string
}

interface DuplicateDetectionProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (txHash: string, isDuplicate: boolean) => void
}

const DuplicateDetection = ({ isOpen, onClose, onConfirm }: DuplicateDetectionProps) => {
  const [duplicates, setDuplicates] = useState<DuplicateTransaction[]>([])
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadDuplicates()
    }
  }, [isOpen])

  const loadDuplicates = async () => {
    try {
      setLoading(true)
      // This would be a new endpoint to get detected duplicates
      const response = await api.get('/api/budget/duplicates')
      if (response.data.ok) {
        setDuplicates(response.data.duplicates)
      }
    } catch (error) {
      console.error('Failed to load duplicates:', error)
      showToast('Failed to load duplicate transactions', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmDuplicate = async (txHash: string, isDuplicate: boolean) => {
    try {
      setProcessing(txHash)
      await api.put(`/api/budget/confirm-duplicate/${txHash}`, null, {
        params: { is_duplicate: isDuplicate }
      })

      showToast(
        `Transaction marked as ${isDuplicate ? 'duplicate' : 'not duplicate'}`,
        'success'
      )

      // Remove from local state
      setDuplicates(prev => prev.filter(dup =>
        dup.tx1_hash !== txHash && dup.tx2_hash !== txHash
      ))

      onConfirm(txHash, isDuplicate)
    } catch (error) {
      showToast(`Failed to update transaction: ${handleApiError(error)}`, 'error')
    } finally {
      setProcessing(null)
    }
  }

  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'text-red-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-blue-400'
  }

  const getSimilarityText = (score: number) => {
    if (score >= 0.8) return 'Very High'
    if (score >= 0.6) return 'High'
    if (score >= 0.4) return 'Medium'
    return 'Low'
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-lg p-6 max-w-4xl w-full mx-4 border border-white/10 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-white">Duplicate Transaction Detection</h2>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Description */}
        <div className="mb-6 p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg">
          <p className="text-blue-400 text-sm">
            🔍 We've detected potential duplicate transactions across your bank accounts.
            Review each pair and confirm whether they are duplicates or separate transactions.
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-white">Loading duplicates...</span>
          </div>
        )}

        {/* No Duplicates */}
        {!loading && duplicates.length === 0 && (
          <div className="text-center py-8">
            <div className="text-white/70 mb-4">
              <svg className="mx-auto h-12 w-12 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-white mb-2">No Duplicates Found</h3>
            <p className="text-white/70">Great! No duplicate transactions were detected in your recent activity.</p>
          </div>
        )}

        {/* Duplicates List */}
        {!loading && duplicates.length > 0 && (
          <div className="space-y-4">
            {duplicates.map((duplicate) => (
              <div key={duplicate.id} className="border border-white/20 rounded-lg p-4 bg-white/5">
                {/* Similarity Score */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-white/70 text-sm">Similarity:</span>
                    <span className={`font-semibold ${getSimilarityColor(duplicate.similarity_score)}`}>
                      {getSimilarityText(duplicate.similarity_score)} ({Math.round(duplicate.similarity_score * 100)}%)
                    </span>
                  </div>
                  <div className="text-white/70 text-sm">
                    Detected: {new Date(duplicate.created_at).toLocaleDateString()}
                  </div>
                </div>

                {/* Transaction Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="space-y-2">
                    <h4 className="text-white font-medium">Transaction 1</h4>
                    <div className="text-sm text-white/70">
                      <div>Hash: {duplicate.tx1_hash.substring(0, 8)}...</div>
                      <div>Status: {duplicate.user_confirmed ? 'Confirmed' : 'Pending'}</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-white font-medium">Transaction 2</h4>
                    <div className="text-sm text-white/70">
                      <div>Hash: {duplicate.tx2_hash.substring(0, 8)}...</div>
                      <div>Status: {duplicate.user_confirmed ? 'Confirmed' : 'Pending'}</div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleConfirmDuplicate(duplicate.tx1_hash, true)}
                    disabled={processing === duplicate.tx1_hash}
                    className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {processing === duplicate.tx1_hash ? 'Processing...' : 'Mark as Duplicate'}
                  </button>
                  <button
                    onClick={() => handleConfirmDuplicate(duplicate.tx1_hash, false)}
                    disabled={processing === duplicate.tx1_hash}
                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {processing === duplicate.tx1_hash ? 'Processing...' : 'Keep Both'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-white/20 rounded-lg text-white hover:bg-white/10 transition-colors"
          >
            Close
          </button>
          <button
            onClick={loadDuplicates}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  )
}

export default DuplicateDetection
