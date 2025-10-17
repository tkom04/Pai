import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Layout from '@/components/Layout'
import api from '@/lib/api'
import { showToast } from '@/lib/errorHandler'

export default function SettingsPage() {
  const router = useRouter()
  const [calendarConnected, setCalendarConnected] = useState(false)
  const [isLoadingCalendar, setIsLoadingCalendar] = useState(true)
  const [isConnecting, setIsConnecting] = useState(false)

  useEffect(() => {
    checkCalendarStatus()

    // Check if we just came back from OAuth
    if (router.query.auth === 'success') {
      showToast('Google Calendar connected successfully!', 'success')
      // Remove the query parameter
      router.replace('/settings', undefined, { shallow: true })
      checkCalendarStatus()
    }
  }, [router.query])

  const checkCalendarStatus = async () => {
    try {
      const response = await api.get('/auth/google/status')
      setCalendarConnected(response.data.authenticated)
    } catch (error) {
      console.error('Failed to check calendar status:', error)
      setCalendarConnected(false)
    } finally {
      setIsLoadingCalendar(false)
    }
  }

  const handleConnectCalendar = async () => {
    setIsConnecting(true)
    try {
      const response = await api.get('/auth/google')
      const authUrl = response.data.authorization_url
      // Redirect to Google OAuth
      window.location.href = authUrl
    } catch (error) {
      showToast('Failed to initiate Google Calendar connection', 'error')
      setIsConnecting(false)
    }
  }

  const handleDisconnectCalendar = async () => {
    if (!confirm('Are you sure you want to disconnect Google Calendar?')) {
      return
    }

    try {
      await api.post('/auth/google/revoke')
      setCalendarConnected(false)
      showToast('Google Calendar disconnected', 'success')
    } catch (error) {
      showToast('Failed to disconnect Google Calendar', 'error')
    }
  }

  return (
    <Layout>
      <div className="p-6 h-full overflow-y-auto bg-gradient-to-br from-black via-gray-900/20 to-black">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-bold mb-2 gradient-text">Settings</h2>
            <p className="text-white/50">Customize your experience</p>
          </div>

          <div className="space-y-6">
            {/* Account Section */}
            <div className="widget-card hover:scale-[1.01] transition-transform duration-300">
              <h3 className="text-lg font-semibold mb-4">Account</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-white/70 mb-2">Email</label>
                  <input
                    type="email"
                    className="input"
                    placeholder="your.email@example.com"
                    disabled
                  />
                </div>
                <div>
                  <label className="block text-sm text-white/70 mb-2">Display Name</label>
                  <input
                    type="text"
                    className="input"
                    placeholder="Your Name"
                  />
                </div>
              </div>
            </div>

            {/* Preferences Section */}
            <div className="widget-card hover:scale-[1.01] transition-transform duration-300">
              <h3 className="text-lg font-semibold mb-4">Preferences</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Notifications</p>
                    <p className="text-sm text-white/50">Receive push notifications</p>
                  </div>
                  <button className="btn-secondary">
                    Enable
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Dark Mode</p>
                    <p className="text-sm text-white/50">Currently enabled</p>
                  </div>
                  <button className="btn-secondary">
                    Toggle
                  </button>
                </div>
              </div>
            </div>

            {/* Integrations Section */}
            <div className="widget-card hover:scale-[1.01] transition-transform duration-300">
              <h3 className="text-lg font-semibold mb-4">Integrations</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">📅</span>
                    <div>
                      <p className="font-medium">Google Calendar</p>
                      {isLoadingCalendar ? (
                        <p className="text-sm text-white/50">Checking status...</p>
                      ) : (
                        <p className="text-sm text-white/50">
                          {calendarConnected ? (
                            <span className="text-green-400">✓ Connected</span>
                          ) : (
                            <span className="text-yellow-400">Not Connected</span>
                          )}
                        </p>
                      )}
                    </div>
                  </div>
                  {!isLoadingCalendar && (
                    calendarConnected ? (
                      <button
                        onClick={handleDisconnectCalendar}
                        className="btn-secondary hover:bg-red-500/20 hover:text-red-400"
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={handleConnectCalendar}
                        disabled={isConnecting}
                        className="btn-secondary hover:bg-green-500/20 hover:text-green-400"
                      >
                        {isConnecting ? (
                          <div className="flex items-center space-x-2">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Connecting...</span>
                          </div>
                        ) : (
                          'Connect Calendar'
                        )}
                      </button>
                    )
                  )}
                </div>
              </div>
            </div>

            {/* About Section */}
            <div className="widget-card hover:scale-[1.01] transition-transform duration-300">
              <h3 className="text-lg font-semibold mb-4">About</h3>
              <p className="text-white/70 text-sm">
                Pai - Your Personal AI Assistant<br />
                Version 1.0.0
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

