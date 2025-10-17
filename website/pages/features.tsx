import Link from 'next/link'

export default function Features() {
  const features = [
    {
      icon: '📅',
      title: 'Smart Calendar',
      description: 'Seamlessly integrate with Google Calendar. View, create, and manage events with natural language commands.',
      details: [
        'Two-way Google Calendar sync',
        'Natural language event creation',
        'Smart scheduling suggestions',
        'Calendar overview and insights'
      ]
    },
    {
      icon: '✅',
      title: 'Intelligent Tasks',
      description: 'Manage your to-do lists with AI assistance. Prioritize, organize, and never miss a deadline.',
      details: [
        'Priority-based task management',
        'Due date tracking and reminders',
        'Category and tag organization',
        'AI-powered task suggestions'
      ]
    },
    {
      icon: '🛍️',
      title: 'Shopping Lists',
      description: 'Create and manage shopping lists effortlessly. Add items by voice or text, share with family.',
      details: [
        'Quick item addition',
        'Category-based organization',
        'Share lists with others',
        'Cross-device synchronization'
      ]
    },
    {
      icon: '🤖',
      title: 'AI Assistant',
      description: 'Your personal AI powered by advanced language models. Ask questions, get insights, automate tasks.',
      details: [
        'Natural language understanding',
        'Context-aware responses',
        'Tool invocation capabilities',
        'Learning from your preferences'
      ]
    },
    {
      icon: '💰',
      title: 'Budget Tracking',
      description: 'Keep track of your finances. Import transactions, categorize spending, and visualize your budget.',
      details: [
        'Transaction import (CSV)',
        'Category-based budgeting',
        'Spending visualization',
        'Monthly budget insights'
      ]
    },
    {
      icon: '🌤️',
      title: 'Weather Integration',
      description: 'Stay informed with real-time weather updates integrated into your dashboard.',
      details: [
        'Real-time weather data',
        'Location-based forecasts',
        'Weather alerts',
        'Dashboard widget'
      ]
    }
  ]

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
            <Link href="/features" className="text-purple-400">Features</Link>
            <Link href="/about" className="hover:text-purple-400 transition">About</Link>
            <Link href="/docs" className="hover:text-purple-400 transition">Docs</Link>
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
            Powerful Features
          </h1>
          <p className="text-xl text-white/70">
            Everything you need to manage your digital life in one beautiful dashboard
          </p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="pb-20 px-6">
        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="glass-medium rounded-2xl p-8 hover:scale-105 transition-all">
              <span className="text-5xl mb-4 block">{feature.icon}</span>
              <h3 className="text-2xl font-bold mb-3">{feature.title}</h3>
              <p className="text-white/70 mb-6">{feature.description}</p>
              <ul className="space-y-2">
                {feature.details.map((detail, i) => (
                  <li key={i} className="flex items-center space-x-2 text-white/60">
                    <span className="text-purple-400">✓</span>
                    <span>{detail}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center glass-medium rounded-3xl p-12">
          <h2 className="text-4xl font-bold mb-6">Ready to Experience Orbit?</h2>
          <p className="text-xl text-white/70 mb-8">
            Start organizing your life with AI-powered intelligence
          </p>
          <a href="http://localhost:3000/login" className="inline-block px-10 py-4 text-lg font-semibold rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:shadow-2xl hover:shadow-purple-500/50 transition-all hover:scale-105">
            Get Started Free →
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

