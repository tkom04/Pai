import Link from 'next/link'

export default function Docs() {
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
            <Link href="/docs" className="text-purple-400">Docs</Link>
          </div>
          <div className="flex space-x-4">
            <Link href="/signup" className="px-6 py-2 rounded-full border border-purple-500 hover:bg-purple-500/10 transition">
              Sign Up
            </Link>
            <a href="http://localhost:3000/login" className="px-6 py-2 rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:shadow-lg hover:shadow-purple-500/50 transition">
              Launch App
            </a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl font-bold mb-6 gradient-text">
            Documentation
          </h1>
          <p className="text-xl text-white/70">
            Everything you need to know to get started with Orbit
          </p>
        </div>
      </section>

      {/* Documentation Content */}
      <section className="pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Sidebar */}
            <div className="md:col-span-1">
              <div className="glass-medium rounded-2xl p-6 sticky top-24">
                <h3 className="font-bold mb-4">Quick Links</h3>
                <ul className="space-y-2 text-sm">
                  <li><a href="#getting-started" className="text-purple-400 hover:text-purple-300">Getting Started</a></li>
                  <li><a href="#calendar" className="text-white/60 hover:text-white">Calendar Setup</a></li>
                  <li><a href="#tasks" className="text-white/60 hover:text-white">Managing Tasks</a></li>
                  <li><a href="#shopping" className="text-white/60 hover:text-white">Shopping Lists</a></li>
                  <li><a href="#ai" className="text-white/60 hover:text-white">AI Assistant</a></li>
                  <li><a href="#budget" className="text-white/60 hover:text-white">Budget Tracking</a></li>
                  <li><a href="#pwa" className="text-white/60 hover:text-white">Install as App</a></li>
                </ul>
              </div>
            </div>

            {/* Main Content */}
            <div className="md:col-span-3 space-y-12">
              {/* Getting Started */}
              <div id="getting-started" className="glass-medium rounded-2xl p-8">
                <h2 className="text-3xl font-bold mb-4 flex items-center">
                  <span className="text-4xl mr-3">🚀</span>
                  Getting Started
                </h2>
                <div className="space-y-4 text-white/70">
                  <p>
                    Welcome to Orbit! Getting started is quick and easy:
                  </p>
                  <ol className="list-decimal list-inside space-y-2 ml-4">
                    <li>Create an account using email or Google Sign-In</li>
                    <li>Connect your Google Calendar (optional but recommended)</li>
                    <li>Explore the dashboard and start adding tasks or shopping items</li>
                    <li>Try asking the AI assistant questions in natural language</li>
                  </ol>
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4 mt-6">
                    <p className="text-purple-300 font-semibold">💡 Pro Tip</p>
                    <p className="text-sm mt-2">
                      Install Orbit as a Progressive Web App for the best experience. Click the install button in your browser or look for &quot;Add to Home Screen&quot; in your mobile browser menu.
                    </p>
                  </div>
                </div>
              </div>

              {/* Calendar Setup */}
              <div id="calendar" className="glass-medium rounded-2xl p-8">
                <h2 className="text-3xl font-bold mb-4 flex items-center">
                  <span className="text-4xl mr-3">📅</span>
                  Calendar Setup
                </h2>
                <div className="space-y-4 text-white/70">
                  <p>
                    Orbit integrates seamlessly with Google Calendar:
                  </p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Navigate to the Calendar page</li>
                    <li>Click &quot;Connect Google Calendar&quot;</li>
                    <li>Authorize Orbit to access your calendar</li>
                    <li>View and manage events directly from Orbit</li>
                  </ul>
                  <p className="mt-4">
                    Once connected, you can create events using natural language with the AI assistant:
                    &quot;Schedule a meeting tomorrow at 2pm&quot;
                  </p>
                </div>
              </div>

              {/* Tasks */}
              <div id="tasks" className="glass-medium rounded-2xl p-8">
                <h2 className="text-3xl font-bold mb-4 flex items-center">
                  <span className="text-4xl mr-3">✅</span>
                  Managing Tasks
                </h2>
                <div className="space-y-4 text-white/70">
                  <p>
                    Stay organized with Orbit&apos;s task management:
                  </p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Create tasks with titles, descriptions, and due dates</li>
                    <li>Assign priorities (low, medium, high)</li>
                    <li>Add categories to organize tasks</li>
                    <li>Mark tasks as complete or archive them</li>
                  </ul>
                  <p className="mt-4">
                    Use the AI assistant: &quot;Add a task to buy groceries tomorrow&quot;
                  </p>
                </div>
              </div>

              {/* Shopping Lists */}
              <div id="shopping" className="glass-medium rounded-2xl p-8">
                <h2 className="text-3xl font-bold mb-4 flex items-center">
                  <span className="text-4xl mr-3">🛍️</span>
                  Shopping Lists
                </h2>
                <div className="space-y-4 text-white/70">
                  <p>
                    Never forget an item with smart shopping lists:
                  </p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Add items quickly with one click</li>
                    <li>Organize by categories (produce, dairy, etc.)</li>
                    <li>Check off items as you shop</li>
                    <li>Share lists with family members</li>
                  </ul>
                </div>
              </div>

              {/* AI Assistant */}
              <div id="ai" className="glass-medium rounded-2xl p-8">
                <h2 className="text-3xl font-bold mb-4 flex items-center">
                  <span className="text-4xl mr-3">🤖</span>
                  AI Assistant
                </h2>
                <div className="space-y-4 text-white/70">
                  <p>
                    Your AI assistant understands natural language commands:
                  </p>
                  <div className="bg-white/5 rounded-lg p-4 font-mono text-sm space-y-2">
                    <p>&quot;What&apos;s on my schedule today?&quot;</p>
                    <p>&quot;Add milk to my shopping list&quot;</p>
                    <p>&quot;Create a task to finish the report by Friday&quot;</p>
                    <p>&quot;What tasks do I have due this week?&quot;</p>
                  </div>
                  <p className="mt-4">
                    The AI can access your calendar, tasks, and shopping lists to provide contextual responses and take actions on your behalf.
                  </p>
                </div>
              </div>

              {/* PWA Installation */}
              <div id="pwa" className="glass-medium rounded-2xl p-8">
                <h2 className="text-3xl font-bold mb-4 flex items-center">
                  <span className="text-4xl mr-3">📱</span>
                  Install as App
                </h2>
                <div className="space-y-4 text-white/70">
                  <p>
                    Install Orbit as a Progressive Web App for the best experience:
                  </p>
                  <div className="space-y-4 mt-4">
                    <div>
                      <h4 className="font-semibold text-white mb-2">On Desktop (Chrome/Edge)</h4>
                      <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                        <li>Click the install icon in the address bar</li>
                        <li>Or go to menu → &quot;Install Orbit&quot;</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-2">On iOS (Safari)</h4>
                      <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                        <li>Tap the share button</li>
                        <li>Select &quot;Add to Home Screen&quot;</li>
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-white mb-2">On Android</h4>
                      <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                        <li>Tap menu → &quot;Add to Home screen&quot;</li>
                        <li>Or follow the install prompt</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
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

