import Link from 'next/link'

export default function About() {
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
            <Link href="/about" className="text-purple-400">About</Link>
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
            About Orbit
          </h1>
          <p className="text-xl text-white/70">
            Your personal AI command center for managing life&apos;s digital complexity
          </p>
        </div>
      </section>

      {/* Story Section */}
      <section className="pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="glass-medium rounded-2xl p-12 mb-12">
            <h2 className="text-3xl font-bold mb-6">Our Mission</h2>
            <p className="text-lg text-white/70 mb-4">
              Orbit was born from a simple idea: managing your digital life shouldn&apos;t be complicated.
              We believe that AI should empower you, not overwhelm you. That&apos;s why we&apos;ve created
              a unified dashboard that brings together all your essential tools in one beautiful,
              intelligent interface.
            </p>
            <p className="text-lg text-white/70">
              Our mission is to give everyone access to powerful AI-driven productivity tools
              while respecting privacy and giving users full control over their data.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <div className="glass-medium rounded-2xl p-8 text-center">
              <div className="text-4xl mb-4">🔒</div>
              <h3 className="text-xl font-bold mb-3">Privacy First</h3>
              <p className="text-white/60">
                Your data belongs to you. We use encryption, secure authentication, and never sell your information.
              </p>
            </div>

            <div className="glass-medium rounded-2xl p-8 text-center">
              <div className="text-4xl mb-4">🌍</div>
              <h3 className="text-xl font-bold mb-3">Open Source</h3>
              <p className="text-white/60">
                Built with transparency. Self-hostable, auditable, and community-driven development.
              </p>
            </div>

            <div className="glass-medium rounded-2xl p-8 text-center">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-xl font-bold mb-3">Performance</h3>
              <p className="text-white/60">
                Lightning fast, works offline, and designed for modern devices with PWA technology.
              </p>
            </div>
          </div>

          <div className="glass-medium rounded-2xl p-12">
            <h2 className="text-3xl font-bold mb-6">Technology Stack</h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-xl font-semibold mb-3 text-purple-400">Frontend</h4>
                <ul className="space-y-2 text-white/70">
                  <li>• Next.js & React</li>
                  <li>• TypeScript</li>
                  <li>• Tailwind CSS</li>
                  <li>• Progressive Web App</li>
                </ul>
              </div>
              <div>
                <h4 className="text-xl font-semibold mb-3 text-blue-400">Backend</h4>
                <ul className="space-y-2 text-white/70">
                  <li>• FastAPI (Python)</li>
                  <li>• Supabase (PostgreSQL)</li>
                  <li>• OpenAI GPT-4</li>
                  <li>• Google Calendar API</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center glass-medium rounded-3xl p-12">
          <h2 className="text-4xl font-bold mb-6">Join the Orbit Community</h2>
          <p className="text-xl text-white/70 mb-8">
            Be part of the future of personal productivity
          </p>
          <a href="http://localhost:3000/login" className="inline-block px-10 py-4 text-lg font-semibold rounded-full bg-gradient-to-r from-purple-600 to-blue-600 hover:shadow-2xl hover:shadow-purple-500/50 transition-all hover:scale-105">
            Get Started Today →
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

