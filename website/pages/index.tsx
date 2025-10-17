"use client"
import { useState, useEffect, useRef } from 'react'
import Head from 'next/head'
import Link from 'next/link'

// Planet definitions for solar system visualization
const PLANET_DEFS = [
  { key: 'mercury', a: 0.387098, period: 87.9691, L0: 252.250906, size: 3 },
  { key: 'venus', a: 0.723332, period: 224.70069, L0: 181.979801, size: 4 },
  { key: 'earth', a: 1.000000, period: 365.256363004, L0: 100.466457, size: 4 },
  { key: 'mars', a: 1.523679, period: 686.97959, L0: 355.433000, size: 3 },
  { key: 'jupiter', a: 5.20260, period: 4332.589, L0: 34.351519, size: 5 },
  { key: 'saturn', a: 9.55491, period: 10759.22, L0: 50.077444, size: 5 },
  { key: 'uranus', a: 19.21845, period: 30685.4, L0: 314.055005, size: 4 },
  { key: 'neptune', a: 30.11039, period: 60189.0, L0: 304.348665, size: 4 },
]

export default function LandingPage() {
  const [showDemoModal, setShowDemoModal] = useState(false)
  // Initialize all planets at 12 o'clock (0 degrees) from the start
  const [planetAngles, setPlanetAngles] = useState<Record<string, number>>(() => {
    const initial: Record<string, number> = {}
    PLANET_DEFS.forEach(p => {
      initial[p.key] = 0
    })
    return initial
  })
  const [solarOpacity, setSolarOpacity] = useState(0.35)
  const solarTimerRef = useRef<NodeJS.Timeout | null>(null)
  const animationRef = useRef<number | null>(null)

  const [formData, setFormData] = useState({
    firstName: '',
    email: '',
    role: ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState('')

  // Calculate days since J2000 epoch
  const daysSinceJ2000 = (t = Date.now()) => {
    const J2000 = Date.UTC(2000, 0, 1, 12, 0, 0)
    return (t - J2000) / 86400000
  }

  // Calculate current angle for a planet (in degrees)
  const getCurrentAngle = (planet: typeof PLANET_DEFS[0]) => {
    const d = daysSinceJ2000()
    return (planet.L0 + 360 * (d / planet.period)) % 360
  }

  // Get position from angle
  const getPositionFromAngle = (planet: typeof PLANET_DEFS[0], angleDeg: number) => {
    const maxAU = PLANET_DEFS[PLANET_DEFS.length - 1].a
    const maxRadiusPx = 180
    const base = 20
    const scale = (maxRadiusPx - base) / Math.sqrt(maxAU)

    const r = base + scale * Math.sqrt(planet.a)
    const angle = (angleDeg * Math.PI) / 180
    const x = r * Math.sin(angle)
    const y = -r * Math.cos(angle)

    return { x, y }
  }

  // Initialize and animate solar system
  useEffect(() => {
    // Calculate final angles for each planet
    const finalAngles: Record<string, number> = {}
    PLANET_DEFS.forEach(p => {
      finalAngles[p.key] = getCurrentAngle(p)
    })

    // Wait for initial render, then animate
    setTimeout(() => {
      const startTime = Date.now()
      const animationDuration = 2500 // 2.5 seconds

      const animate = () => {
        const elapsed = Date.now() - startTime
        const progress = Math.min(elapsed / animationDuration, 1)

        // Ease-in-out for smooth start and end
        const eased = progress < 0.5
          ? 2 * progress * progress
          : 1 - Math.pow(-2 * progress + 2, 2) / 2

        const currentAngles: Record<string, number> = {}
        PLANET_DEFS.forEach(p => {
          // Each planet travels from 0° to its final angle
          // Add one full rotation (360°) so they all go around once before settling
          const targetAngle = finalAngles[p.key]
          const totalTravel = 360 + targetAngle
          currentAngles[p.key] = eased * totalTravel
        })

        setPlanetAngles(currentAngles)

        if (progress < 1) {
          animationRef.current = requestAnimationFrame(animate)
        } else {
          // Animation complete - set to final positions
          setPlanetAngles(finalAngles)
          // Start interval to update every minute
          solarTimerRef.current = setInterval(() => {
            const updatedAngles: Record<string, number> = {}
            PLANET_DEFS.forEach(p => {
              updatedAngles[p.key] = getCurrentAngle(p)
            })
            setPlanetAngles(updatedAngles)
          }, 60000)
        }
      }

      // Start animation
      animationRef.current = requestAnimationFrame(animate)
    }, 100)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (solarTimerRef.current) {
        clearInterval(solarTimerRef.current)
      }
    }
  }, [])

  // Fade out solar system on scroll (mobile only)
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY
      // Fade from 0.35 at top to 0 at ~1400px scroll (around "Less juggling" section)
      const maxScroll = 1400
      const newOpacity = Math.max(0, 0.35 - (scrollY / maxScroll) * 0.35)
      setSolarOpacity(newOpacity)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError('Please enter a valid email')
      return
    }

    if (!formData.firstName || !formData.role) {
      setError('Please fill in all required fields')
      return
    }

    setSubmitting(true)

    try {
      // Store locally for UX continuity
      localStorage.setItem('orbit_waitlist', JSON.stringify({ ...formData, ts: Date.now() }))

      // Simulate API call (replace with your actual endpoint later)
      await new Promise(r => setTimeout(r, 800))

      setSuccess(true)
      setFormData({ firstName: '', email: '', role: '' })
    } catch (err) {
      console.error('Waitlist signup error:', err)
      setError('Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const currentYear = new Date().getFullYear()

  // Calculate orbital ring radius for solar system (perfect circles)
  const getOrbitalStyles = (planet: typeof PLANET_DEFS[0]) => {
    const maxAU = PLANET_DEFS[PLANET_DEFS.length - 1].a
    const maxRadiusPx = 180
    const base = 20
    const scale = (maxRadiusPx - base) / Math.sqrt(maxAU)
    const r = base + scale * Math.sqrt(planet.a)

    return {
      width: `${r * 2}px`,
      height: `${r * 2}px`, // Perfect circle - no perspective distortion
      marginLeft: `-${r}px`,
      marginTop: `-${r}px`
    }
  }

  return (
    <>
      <Head>
        <title>Orbit — Your tasks revolve around you</title>
        <meta name="description" content="Shopping lists, todos, Open Banking, and Google Calendar — orchestrated by an AI that actually assists you." />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
      </Head>

      <div className="bg-midnight text-snow font-sans selection:bg-violet/30 min-h-screen">
        {/* Top Banner */}
        <div className="relative overflow-hidden">
          <div className="bg-gradient-to-r from-violet/30 to-transparent text-snow/90 text-xs md:text-sm py-2 text-center">
            <span className="px-3">Shopping lists • Todos • Open Banking • Google Calendar — all coordinated by a helpful AI.</span>
          </div>
        </div>

        {/* Navigation */}
        <header className="sticky top-0 z-50 backdrop-blur bg-midnight/70 border-b border-white/5">
          <div className="max-w-7xl mx-auto px-4 md:px-6">
            <div className="h-16 flex items-center justify-between gap-4">
              <Link href="#top" className="inline-flex items-center gap-2">
                <svg width="26" height="26" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow">
                  <circle cx="32" cy="32" r="10" fill="url(#g)"/>
                  <g filter="url(#f)">
                    <circle cx="32" cy="32" r="2.5" fill="white"/>
                  </g>
                  <g className="animate-spinSlow origin-center">
                    <ellipse cx="32" cy="32" rx="22" ry="10" stroke="#6E44FF" strokeOpacity=".35" strokeWidth="2"/>
                  </g>
                  <defs>
                    <linearGradient id="g" x1="22" y1="22" x2="42" y2="42" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#6E44FF"/>
                      <stop offset="1" stopColor="#B39CFF"/>
                    </linearGradient>
                    <filter id="f" x="26" y="26" width="12" height="12">
                      <feGaussianBlur stdDeviation="1.2"/>
                    </filter>
                  </defs>
                </svg>
                <span className="font-bold tracking-tight text-lg">Orbit</span>
              </Link>
              <nav className="hidden md:flex items-center gap-6 text-sm text-white/80">
                <a href="#how" className="hover:text-white transition">How it works</a>
                <a href="#benefits" className="hover:text-white transition">Why Orbit</a>
                <a href="#integrations" className="hover:text-white transition">Integrations</a>
                <a href="#faq" className="hover:text-white transition">FAQ</a>
              </nav>
              <div className="ml-auto md:ml-0 flex items-center gap-3">
                <a href="http://localhost:3000/login" className="text-sm text-white/70 hover:text-white transition">
                  Sign In
                </a>
                <a href="#waitlist" className="inline-flex items-center justify-center px-4 py-2 rounded-xl bg-violet text-white font-semibold shadow-glow hover:scale-[1.02] transition">
                  Get early access
                </a>
              </div>
            </div>
          </div>
        </header>

        {/* Solar System - Mobile Sticky Background */}
        <div
          className="fixed top-40 left-1/2 -translate-x-1/2 md:hidden flex items-center justify-center -z-0 pointer-events-none transition-opacity duration-300"
          style={{ opacity: solarOpacity }}
        >
          <div className="relative scale-75">
            {/* Solar system with accurate planetary positions */}
            <div className="absolute inset-0 flex items-center justify-center select-none">
              <div className="relative">
                {PLANET_DEFS.map(planet => {
                  const styles = getOrbitalStyles(planet)
                  const angle = planetAngles[planet.key] || 0
                  const pos = getPositionFromAngle(planet, angle)

                  return (
                    <div key={`mobile-${planet.key}`}>
                      {/* Perfect circular orbit ring */}
                      <div
                        className="absolute left-1/2 top-1/2 border border-white/20 rounded-full"
                        style={styles}
                      />
                      {/* Planet */}
                      <span
                        className="absolute left-1/2 top-1/2 rounded-full bg-white/80"
                        style={{
                          width: `${planet.size}px`,
                          height: `${planet.size}px`,
                          marginLeft: `-${planet.size / 2}px`,
                          marginTop: `-${planet.size / 2}px`,
                          transform: `translate(${pos.x}px, ${pos.y}px)`
                        }}
                      />
                    </div>
                  )
                })}

                {/* The Sun */}
                <span className="relative block w-4 h-4 rounded-full bg-white shadow-glow"></span>
              </div>
            </div>
          </div>
        </div>

        {/* Hero */}
        <section id="top" className="relative overflow-hidden">
          {/* Starfield background */}
        <div className="absolute inset-0">
            <div className="absolute inset-0" style={{
              background: `radial-gradient(2px 2px at 20% 30%, rgba(255,255,255,.25) 50%, transparent 51%),
                          radial-gradient(1.5px 1.5px at 80% 20%, rgba(255,255,255,.15) 50%, transparent 51%),
                          radial-gradient(1.2px 1.2px at 60% 70%, rgba(255,255,255,.2) 50%, transparent 51%),
                          radial-gradient(1px 1px at 30% 80%, rgba(255,255,255,.15) 50%, transparent 51%)`,
              opacity: 0.12,
              pointerEvents: 'none'
            }}></div>
        </div>

          <div className="absolute -z-10 inset-0 bg-[radial-gradient(60%_50%_at_50%_0%,rgba(110,68,255,.16)_0%,transparent_60%)]"></div>

          <div className="max-w-7xl mx-auto px-4 md:px-6 pt-16 md:pt-28 pb-16 relative z-10">
            <div className="grid md:grid-cols-2 gap-10 items-center">
              <div className="relative z-20">
                <h1 className="text-4xl md:text-6xl leading-tight font-extrabold tracking-tight">
                  Make life revolve around <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">you</span>
          </h1>
                <p className="mt-4 text-white/80 text-lg md:text-xl max-w-xl">
                  An AI that actually assists <span className="font-semibold">you</span> — not your IQ. It brings together shopping lists, todos, Open Banking, and Google Calendar so the right thing shows up at the right time.
                </p>
                <div className="mt-8 flex flex-col sm:flex-row gap-3">
                  <a href="#waitlist" className="inline-flex justify-center items-center px-5 py-3 rounded-xl bg-violet font-semibold shadow-glow hover:scale-[1.02] transition">
                    Join the waitlist
                  </a>
                  <button
                    onClick={() => setShowDemoModal(true)}
                    className="inline-flex justify-center items-center px-5 py-3 rounded-xl border border-white/15 hover:border-white/30 hover:bg-white/5 transition"
                  >
                    ▶︎ See a 90‑sec tour
                  </button>
                </div>

                {/* Value bullets */}
                <ul className="mt-6 grid grid-cols-2 md:grid-cols-2 gap-2 text-sm text-white/70">
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-violet"></span> Shopping lists
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-violet"></span> Todos
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-violet"></span> Google Calendar
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-violet"></span> Open Banking
                  </li>
                </ul>
          </div>

              {/* Solar System Visualization - Desktop Only */}
              <div className="hidden md:block relative h-[360px] md:h-[460px]">
                <div className="absolute inset-0 grid place-items-center">
                  <div className="relative">
                    {/* Solar system with accurate planetary positions */}
                    <div className="absolute inset-0 flex items-center justify-center select-none">
                      <div className="relative">
                        {PLANET_DEFS.map(planet => {
                          const styles = getOrbitalStyles(planet)
                          const angle = planetAngles[planet.key] || 0
                          const pos = getPositionFromAngle(planet, angle)

                          return (
                            <div key={planet.key}>
                              {/* Perfect circular orbit ring */}
                              <div
                                className="absolute left-1/2 top-1/2 border border-white/10 rounded-full"
                                style={styles}
                              />
                              {/* Planet */}
                              <span
                                title={planet.key.charAt(0).toUpperCase() + planet.key.slice(1)}
                                className="absolute left-1/2 top-1/2 rounded-full bg-white/95 cursor-help"
                                style={{
                                  width: `${planet.size}px`,
                                  height: `${planet.size}px`,
                                  marginLeft: `-${planet.size / 2}px`,
                                  marginTop: `-${planet.size / 2}px`,
                                  transform: `translate(${pos.x}px, ${pos.y}px)`
                                }}
                              />
                            </div>
                          )
                        })}

                        {/* The Sun */}
                        <span className="relative block w-4 h-4 rounded-full bg-white shadow-glow"></span>
                      </div>
                    </div>
            </div>
            </div>
            </div>
            </div>

            {/* Trust bar */}
            <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
              <div className="rounded-xl border border-white/10 p-4 bg-white/5">No spam. Unsubscribe anytime.</div>
              <div className="rounded-xl border border-white/10 p-4 bg-white/5">Keep data on your device whenever possible.</div>
              <div className="rounded-xl border border-white/10 p-4 bg-white/5">Built to work with your tools — not replace them.</div>
          </div>
        </div>
      </section>

        {/* How it works */}
        <section id="how" className="relative py-20">
          <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_bottom,rgba(255,255,255,.04),transparent)]"></div>
          <div className="max-w-7xl mx-auto px-4 md:px-6">
            <h2 className="text-3xl md:text-4xl font-bold">How Orbit keeps you moving</h2>
            <p className="mt-2 text-white/70 max-w-2xl">Three lightweight loops that reduce mental load without losing control.</p>

            <div className="mt-10 grid md:grid-cols-3 gap-5">
              <div className="rounded-2xl border border-white/10 p-6 bg-white/[0.04] hover:bg-white/[0.06] transition">
                <div className="text-2xl">🧠</div>
                <h3 className="mt-3 font-semibold text-xl">Daily Brief</h3>
                <p className="mt-2 text-white/70">A morning snapshot that merges calendar, tasks and context — so you know exactly what matters next.</p>
              </div>
              <div className="rounded-2xl border border-white/10 p-6 bg-white/[0.04] hover:bg-white/[0.06] transition">
                <div className="text-2xl">🔗</div>
                <h3 className="mt-3 font-semibold text-xl">Orchestration</h3>
                <p className="mt-2 text-white/70">Orbit coordinates your tools and routines; tasks & shopping lists live in Supabase (self‑hosted).</p>
              </div>
              <div className="rounded-2xl border border-white/10 p-6 bg-white/[0.04] hover:bg-white/[0.06] transition">
                <div className="text-2xl">🎯</div>
                <h3 className="mt-3 font-semibold text-xl">Focus Nudges</h3>
                <p className="mt-2 text-white/70">Gentle, context‑aware prompts that keep you on track — never naggy, always optional.</p>
              </div>
            </div>

            <div className="mt-8 text-sm text-white/60">Works great for overwhelmed professionals, working parents, and solo builders.</div>
          </div>
        </section>

        {/* Benefits */}
        <section id="benefits" className="py-20">
          <div className="max-w-7xl mx-auto px-4 md:px-6">
            <h2 className="text-3xl md:text-4xl font-bold">Less juggling. More momentum.</h2>
            <p className="mt-2 text-white/70 max-w-2xl">Designed for busy humans — not productivity maximalists.</p>

            <div className="mt-10 grid md:grid-cols-3 gap-5">
              <div className="rounded-2xl border border-white/10 p-6 bg-white/[0.04]">
                <h3 className="font-semibold text-lg">Privacy‑first</h3>
                <p className="mt-2 text-white/70">Default to processing on your device where possible. You stay in control of your data.</p>
              </div>
              <div className="rounded-2xl border border-white/10 p-6 bg-white/[0.04]">
                <h3 className="font-semibold text-lg">Fewer apps</h3>
                <p className="mt-2 text-white/70">Orbit sits on top of the tools you already use, reducing switching and duplication.</p>
              </div>
              <div className="rounded-2xl border border-white/10 p-6 bg-white/[0.04]">
                <h3 className="font-semibold text-lg">Momentum by design</h3>
                <p className="mt-2 text-white/70">Small wins add up — briefings, one‑tap deferrals, and gentle automation keep you moving.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Integrations */}
        <section id="integrations" className="py-20 relative">
          <div className="max-w-7xl mx-auto px-4 md:px-6">
            <h2 className="text-3xl md:text-4xl font-bold">Plays nice with your stack</h2>
            <p className="mt-2 text-white/70 max-w-2xl">Shopping lists & todos live in your Supabase. Google Calendar connects on day one. Banking connects via Open Banking when enabled.</p>

            <div className="mt-10 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              <div className="rounded-xl border border-white/10 p-3 text-center bg-white/[0.04]">Google Calendar</div>
              <div className="rounded-xl border border-white/10 p-3 text-center bg-white/[0.04]">Open Banking</div>
              <div className="rounded-xl border border-white/10 p-3 text-center bg-white/[0.04]">Supabase (tasks & lists)</div>
            </div>

            <div className="mt-3 text-xs text-white/60">Supabase is self‑hosted only (no BYO/managed option). Open Banking connections are optional.</div>
          </div>
        </section>

        {/* Waitlist */}
        <section id="waitlist" className="py-20 relative">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(40%_60%_at_50%_100%,rgba(110,68,255,.12),transparent)]"></div>
          <div className="max-w-3xl mx-auto px-4 md:px-6">
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 md:p-8">
              <h2 className="text-2xl md:text-3xl font-bold">Get early access</h2>
              <p className="mt-2 text-white/70">Be first to try Orbit. We'll invite small cohorts, then open wider.</p>

              <form onSubmit={handleSubmit} className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label htmlFor="firstName" className="text-sm text-white/70">First name</label>
                  <input
                    id="firstName"
                    name="firstName"
                    value={formData.firstName}
                    onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                    required
                    className="mt-1 w-full rounded-xl bg-white/[0.06] border border-white/10 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet/60 text-white"
                  />
                </div>
                <div className="md:col-span-2">
                  <label htmlFor="email" className="text-sm text-white/70">Email</label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    className="mt-1 w-full rounded-xl bg-white/[0.06] border border-white/10 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet/60 text-white"
                  />
                </div>
                <div className="md:col-span-3">
                  <label htmlFor="role" className="text-sm text-white/70">Which best describes you?</label>
                  <select
                    id="role"
                    name="role"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    required
                    className="mt-1 w-full rounded-xl bg-white/[0.06] border border-white/10 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet/60 text-white"
                  >
                    <option value="">Select…</option>
                    <option>Overwhelmed professional</option>
                    <option>Working parent</option>
                    <option>Senior executive</option>
                    <option>Freelancer / solopreneur</option>
                    <option>Other</option>
                  </select>
                </div>
                <div className="md:col-span-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-xs text-white/60">No spam. Unsubscribe anytime.</p>
                  <button
                    className="inline-flex justify-center items-center rounded-xl bg-violet px-5 py-3 font-semibold shadow-glow hover:scale-[1.02] transition disabled:opacity-50 disabled:cursor-not-allowed"
                    type="submit"
                    disabled={submitting}
                  >
                    {submitting ? 'Joining...' : 'Join the waitlist'}
                  </button>
                </div>
              </form>

              {success && (
                <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-emerald-200 animate-fadeIn">
                  Thanks — you're on the list. Check your inbox shortly.
                </div>
              )}

              {error && (
                <div className="mt-4 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-rose-200 animate-fadeIn">
                  {error}
            </div>
              )}
          </div>
        </div>
      </section>

        {/* FAQ */}
        <section id="faq" className="py-20">
          <div className="max-w-5xl mx-auto px-4 md:px-6">
            <h2 className="text-3xl md:text-4xl font-bold">Questions, answered</h2>
            <div className="mt-8 divide-y divide-white/10 rounded-2xl border border-white/10 bg-white/[0.04]">
              <details className="group p-5 open:bg-white/[0.02]">
                <summary className="flex cursor-pointer list-none items-center justify-between text-lg font-semibold">
                  How private is Orbit?
                  <span className="ml-4 text-white/50 group-open:rotate-45 transition">+</span>
                </summary>
                <p className="mt-3 text-white/70">We aim to do as much as possible on your device. When the cloud is required, we minimize data and retain it only as long as necessary.</p>
              </details>
              <details className="group p-5">
                <summary className="flex cursor-pointer list-none items-center justify-between text-lg font-semibold">
                  Do I need to change tools?
                  <span className="ml-4 text-white/50 group-open:rotate-45 transition">+</span>
                </summary>
                <p className="mt-3 text-white/70">No. Orbit sits on top of your existing stack — it connects, coordinates, and reduces switching.</p>
              </details>
              <details className="group p-5">
                <summary className="flex cursor-pointer list-none items-center justify-between text-lg font-semibold">
                  When can I try it?
                  <span className="ml-4 text-white/50 group-open:rotate-45 transition">+</span>
                </summary>
                <p className="mt-3 text-white/70">We're inviting small groups from the waitlist first to shape the product, then opening more widely.</p>
              </details>
            </div>
        </div>
      </section>

      {/* Footer */}
        <footer className="py-10 border-t border-white/10">
          <div className="max-w-7xl mx-auto px-4 md:px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-white/60">
            <div>© {currentYear} Orbit</div>
            <div className="flex items-center gap-4">
              <a className="hover:text-white transition" href="#waitlist">Get early access</a>
              <a className="hover:text-white transition" href="#faq">FAQ</a>
              <a className="hover:text-white transition" href="#top">Back to top</a>
            </div>
          </div>
        </footer>

        {/* Demo Modal */}
        {showDemoModal && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4" onClick={() => setShowDemoModal(false)}>
            <div className="max-w-3xl w-full rounded-2xl overflow-hidden border border-white/10 bg-midnight" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-center justify-between p-4 border-b border-white/10">
                <div className="font-semibold">Orbit — 90‑second tour</div>
                <button onClick={() => setShowDemoModal(false)} className="text-white/70 hover:text-white transition">✕</button>
              </div>
              <div className="p-4">
                <div className="w-full aspect-video rounded-xl bg-white/[0.06] grid place-items-center text-white/60 text-sm">
                  (Embed your Loom/YouTube here)
                </div>
          </div>
        </div>
        </div>
        )}
    </div>
    </>
  )
}
