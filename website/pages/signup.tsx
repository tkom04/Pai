import Link from 'next/link'
import { useRouter } from 'next/router'

export default function Signup() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <nav className="fixed w-full z-50 bg-black/80 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-3xl">🌌</span>
            <span className="text-2xl font-bold gradient-text">Orbit</span>
          </Link>
          <div className="hidden md:flex space-x-8">
            <Link href="/features" className="hover:text-purple-400 transition">Features</Link>
            <Link href="/about" className="hover:text-purple-400 transition">About</Link>
            <Link href="/docs" className="hover:text-purple-400 transition">Docs</Link>
          </div>
          <div className="flex space-x-4">
            <a href="http://localhost:3000/login" className="px-6 py-2 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:shadow-lg hover:shadow-purple-500/50 transition">
              Launch App
            </a>
          </div>
        </div>
      </nav>

      {/* Signup Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="glass-medium rounded-3xl p-12">
            <h1 className="text-5xl font-bold mb-6 gradient-text">
              Ready to Join Orbit?
            </h1>
            <p className="text-xl text-white/70 mb-12">
              Start your journey to effortless productivity with AI-powered organization
            </p>

            {/* Benefits */}
            <div className="grid md:grid-cols-3 gap-6 mb-12">
              <div className="text-center">
                <div className="text-4xl mb-3">🚀</div>
                <h3 className="font-semibold mb-2">Quick Setup</h3>
                <p className="text-sm text-white/60">Get started in under 2 minutes</p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-3">💳</div>
                <h3 className="font-semibold mb-2">Free to Start</h3>
                <p className="text-sm text-white/60">No credit card required</p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-3">🔒</div>
                <h3 className="font-semibold mb-2">Secure & Private</h3>
                <p className="text-sm text-white/60">Your data stays yours</p>
              </div>
            </div>

            {/* CTA Button */}
            <a
              href="http://localhost:3000/login"
              className="inline-block px-12 py-4 text-xl font-semibold rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:shadow-2xl hover:shadow-purple-500/50 transition-all hover:scale-105"
            >
              Create Your Account →
            </a>

            <p className="mt-6 text-sm text-white/50">
              Already have an account?{' '}
              <a href="http://localhost:3000/login" className="text-purple-400 hover:text-purple-300">
                Sign in
              </a>
            </p>
          </div>
        </div>
      </section>

      {/* What You Get */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-12 gradient-text">
            What You Get With Orbit
          </h2>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="glass-subtle rounded-xl p-6 flex items-start space-x-4">
              <span className="text-3xl">📅</span>
              <div>
                <h3 className="text-lg font-semibold mb-2">Smart Calendar Sync</h3>
                <p className="text-white/60">Connect with Google Calendar and manage your schedule with AI</p>
              </div>
            </div>
            <div className="glass-subtle rounded-xl p-6 flex items-start space-x-4">
              <span className="text-3xl">✅</span>
              <div>
                <h3 className="text-lg font-semibold mb-2">Task Management</h3>
                <p className="text-white/60">Organize tasks with priorities, categories, and due dates</p>
              </div>
            </div>
            <div className="glass-subtle rounded-xl p-6 flex items-start space-x-4">
              <span className="text-3xl">🛍️</span>
              <div>
                <h3 className="text-lg font-semibold mb-2">Shopping Lists</h3>
                <p className="text-white/60">Create and share shopping lists across devices</p>
              </div>
            </div>
            <div className="glass-subtle rounded-xl p-6 flex items-start space-x-4">
              <span className="text-3xl">🤖</span>
              <div>
                <h3 className="text-lg font-semibold mb-2">AI Assistant</h3>
                <p className="text-white/60">Natural language commands and intelligent automation</p>
              </div>
            </div>
            <div className="glass-subtle rounded-xl p-6 flex items-start space-x-4">
              <span className="text-3xl">💰</span>
              <div>
                <h3 className="text-lg font-semibold mb-2">Budget Tracking</h3>
                <p className="text-white/60">Track expenses and manage your finances</p>
              </div>
            </div>
            <div className="glass-subtle rounded-xl p-6 flex items-start space-x-4">
              <span className="text-3xl">📱</span>
              <div>
                <h3 className="text-lg font-semibold mb-2">PWA Support</h3>
                <p className="text-white/60">Install as an app on any device, works offline</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Join Thousands of Users</h2>
          <p className="text-white/70 mb-8">
            Experience the future of personal productivity
          </p>
          <a
            href="http://localhost:3000/login"
            className="inline-block px-10 py-4 text-lg font-semibold rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:shadow-2xl hover:shadow-purple-500/50 transition-all hover:scale-105"
          >
            Start Free Now →
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-12 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center space-x-2 mb-6 md:mb-0">
            <span className="text-3xl">🌌</span>
            <span className="text-xl font-bold">Orbit</span>
          </div>
          <div className="flex space-x-8 text-white/60">
            <Link href="/features" className="hover:text-white transition">Features</Link>
            <Link href="/about" className="hover:text-white transition">About</Link>
            <Link href="/docs" className="hover:text-white transition">Docs</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}

