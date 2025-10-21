"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'

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

interface BankConnectionCardProps {
  connection: BankConnection
  onRevoke: (connectionId: string) => void
  onSync: (connectionId: string) => void
}

const BankConnectionCard = ({ connection, onRevoke, onSync }: BankConnectionCardProps) => {
  const [isRevoking, setIsRevoking] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)

  const handleRevoke = async () => {
    if (!confirm(`Are you sure you want to revoke access to ${connection.institution_display_name}? This will delete all cached data.`)) {
      return
    }

    setIsRevoking(true)
    try {
      await api.delete(`/api/banking/revoke/${connection.id}`)
      showToast(`${connection.institution_display_name} disconnected successfully`, 'success')
      onRevoke(connection.id)
    } catch (error) {
      showToast(`Failed to revoke access: ${handleApiError(error)}`, 'error')
    } finally {
      setIsRevoking(false)
    }
  }

  const handleSync = async () => {
    setIsSyncing(true)
    try {
      // Trigger budget refresh which will sync all accounts
      await api.post('/api/budget/refresh', {}, {
        params: { lookback_days: 90 }
      })
      showToast(`${connection.institution_display_name} synced successfully`, 'success')
      onSync(connection.id)
    } catch (error) {
      showToast(`Failed to sync: ${handleApiError(error)}`, 'error')
    } finally {
      setIsSyncing(false)
    }
  }

  const handleExtend = async () => {
    if (!confirm(`Extend access to ${connection.institution_display_name}? This will renew your bank connection.`)) {
      return
    }

    setIsSyncing(true)
    try {
      await api.post(`/api/banking/extend-connection/${connection.id}`)
      showToast(`Connection to ${connection.institution_display_name} extended successfully!`, 'success')
      onSync(connection.id)
    } catch (error) {
      const errorData = error.response?.data
      if (errorData?.error === 'validation_error') {
        // TrueLayer validation error - show specific details
        const details = errorData.details || {}
        const errors = details.errors || {}

        // Check for specific consent screen error
        const consentError = Object.values(errors).flat().find((error: string) =>
          error.includes('user_has_reconfirmed_consent') || error.includes('consent screen')
        )

        if (consentError) {
          showToast(`Consent screen review required. Please submit your TrueLayer consent screen for review.`, 'info')
        } else {
          const missingFields = Object.keys(details).filter(key =>
            details[key] && details[key].includes('required')
          )
          if (missingFields.length > 0) {
            showToast(`Configuration error: Missing ${missingFields.join(', ')}. Please check your TrueLayer settings.`, 'error')
          } else {
            showToast(`Configuration error: ${errorData.message}`, 'error')
          }
        }
      } else if (errorData?.error === 'reauth_required') {
        showToast(`Connection expired. Please reconnect ${connection.institution_display_name}.`, 'warning')
      } else if (errorData?.error === 'consent_required') {
        showToast(`Consent required. Please confirm access to ${connection.institution_display_name}.`, 'info')
      } else {
        showToast(`Failed to extend connection: ${handleApiError(error)}`, 'error')
      }
    } finally {
      setIsSyncing(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-400'
      case 'expired': return 'text-yellow-400'
      case 'revoked': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return 'Active'
      case 'expired': return 'Expired'
      case 'revoked': return 'Revoked'
      default: return 'Unknown'
    }
  }

  const getExpiryText = () => {
    if (connection.days_until_expiry === null) return 'Unknown'
    if (connection.days_until_expiry <= 0) return 'Expired'
    if (connection.days_until_expiry <= 7) return `Expires in ${connection.days_until_expiry} days`
    if (connection.days_until_expiry <= 30) return `Expires in ${connection.days_until_expiry} days`
    return `Expires in ${connection.days_until_expiry} days`
  }

  const getExpiryColor = () => {
    if (connection.days_until_expiry === null) return 'text-gray-400'
    if (connection.days_until_expiry <= 0) return 'text-red-400'
    if (connection.days_until_expiry <= 7) return 'text-yellow-400'
    if (connection.days_until_expiry <= 30) return 'text-orange-400'
    return 'text-green-400'
  }

  const formatLastSync = () => {
    if (!connection.last_sync) return 'Never'
    try {
      const date = new Date(connection.last_sync)
      return date.toLocaleString()
    } catch {
      return 'Unknown'
    }
  }

  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-6 hover:bg-white/10 transition-colors duration-200">
      {/* Header with logo and status */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {/* Bank logo placeholder - in real implementation, you'd use actual logos */}
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">
              {connection.institution_display_name.charAt(0)}
            </span>
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg">
              {connection.institution_display_name}
            </h3>
            <p className="text-white/70 text-sm">
              {connection.institution_id}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className={`text-sm font-medium ${getStatusColor(connection.status)}`}>
            {getStatusText(connection.status)}
          </div>
          <div className={`text-xs ${getExpiryColor()}`}>
            {getExpiryText()}
          </div>
        </div>
      </div>

      {/* Connection details */}
      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-white/70">Last sync:</span>
          <span className="text-white">{formatLastSync()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-white/70">Connected:</span>
          <span className="text-white">
            {new Date(connection.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex space-x-2">
        <button
          onClick={handleSync}
          disabled={isSyncing || connection.status !== 'active'}
          className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          {isSyncing ? 'Syncing...' : 'Sync'}
        </button>
        <button
          onClick={handleExtend}
          disabled={isSyncing}
          className="flex-1 bg-green-600 text-white px-3 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          {isSyncing ? 'Extending...' : 'Extend'}
        </button>
        <button
          onClick={handleRevoke}
          disabled={isRevoking}
          className="flex-1 bg-red-600 text-white px-3 py-2 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          {isRevoking ? 'Revoking...' : 'Revoke'}
        </button>
      </div>

      {/* Status indicator */}
      {connection.status === 'expired' && (
        <div className="mt-4 p-3 bg-yellow-500/20 border border-yellow-500/30 rounded-lg">
          <p className="text-yellow-400 text-sm">
            ⚠️ This connection has expired. Please reconnect to continue syncing.
          </p>
        </div>
      )}

      {connection.status === 'revoked' && (
        <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
          <p className="text-red-400 text-sm">
            🚫 This connection has been revoked. All data has been deleted.
          </p>
        </div>
      )}
    </div>
  )
}

export default BankConnectionCard
