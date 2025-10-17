"use client"
import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import FloatingAiButton from './widgets/FloatingAiButton'

const navigationItems = [
  { id: 'dashboard', href: '/dashboard', icon: '🏠', label: 'Dashboard' },
  { id: 'calendar', href: '/calendar', icon: '📅', label: 'Calendar' },
  { id: 'tasks', href: '/tasks', icon: '✅', label: 'Tasks' },
  { id: 'shopping', href: '/shopping', icon: '🛍️', label: 'Shopping' },
  { id: 'budget', href: '/budget', icon: '💰', label: 'Budget' },
  { id: 'settings', href: '/settings', icon: '⚙️', label: 'Settings' },
]

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const router = useRouter()
  const [sidebarExpanded, setSidebarExpanded] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const sidebarRef = useRef<HTMLDivElement>(null)

  // Detect mobile screen
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  // Auto-collapse sidebar when route changes
  useEffect(() => {
    const handleRouteChange = () => {
      if (sidebarExpanded) {
        setTimeout(() => setSidebarExpanded(false), 300)
      }
    }

    router.events?.on('routeChangeComplete', handleRouteChange)
    return () => {
      router.events?.off('routeChangeComplete', handleRouteChange)
    }
  }, [router.events, sidebarExpanded])

  // Click outside to close expanded sidebar
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (sidebarExpanded && sidebarRef.current && !sidebarRef.current.contains(event.target as Node)) {
        setSidebarExpanded(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [sidebarExpanded])

  // Get current page label for top bar
  const getCurrentPageLabel = () => {
    const currentItem = navigationItems.find(item => item.href === router.pathname)
    return currentItem?.label || 'Dashboard'
  }

  return (
    <div className="h-screen bg-black flex">
      {/* Desktop Sidebar */}
      {!isMobile && (
        <div
          ref={sidebarRef}
          className={`desktop-nav bg-black/50 backdrop-blur-xl border-r border-white/10 transition-all duration-300 ${
            sidebarExpanded ? 'w-64' : 'w-16'
          }`}
        >
          {/* Logo/Toggle */}
          <div className="p-4 border-b border-white/10">
            <button
              onClick={() => setSidebarExpanded(!sidebarExpanded)}
              className="w-full flex items-center justify-center hover:bg-white/10 rounded-lg p-2 transition-colors"
            >
              <span className="text-xl">{sidebarExpanded ? '←' : '☰'}</span>
            </button>
          </div>

          {/* Navigation */}
          <nav className="p-2">
            {navigationItems.map((item) => {
              const isActive = router.pathname === item.href
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`w-full flex items-center ${
                    sidebarExpanded ? 'justify-start' : 'justify-center'
                  } px-3 py-3 mb-1 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-purple-600 text-white'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <span className="text-xl">{item.icon}</span>
                  {sidebarExpanded && (
                    <span className="ml-3 font-medium animate-fadeIn">{item.label}</span>
                  )}
                </Link>
              )
            })}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="glass-subtle border-b border-white/10 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">{getCurrentPageLabel()}</h2>
            <div className="flex items-center space-x-4">
              <button className="icon-btn">
                <span>🔔</span>
              </button>
              <button className="icon-btn">
                <span>👤</span>
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      {isMobile && (
        <div className="mobile-nav fixed bottom-0 left-0 right-0 glass-medium border-t border-white/20 px-2 py-2 z-40">
          <div className="flex justify-around items-center">
            {navigationItems.slice(0, 6).map((item) => {
              const isActive = router.pathname === item.href
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  className={`flex flex-col items-center p-2 rounded-lg transition-colors ${
                    isActive
                      ? 'text-purple-400'
                      : 'text-white/50'
                  }`}
                >
                  <span className="text-xl mb-1">{item.icon}</span>
                  <span className="text-xs">{item.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      )}

      {/* Floating AI Button */}
      <FloatingAiButton />
    </div>
  )
}

