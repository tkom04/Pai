/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        ink: '#0B0B10',
        midnight: '#0B0B10',
        snow: '#FFFFFF',
        violet: '#6E44FF',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'Helvetica', 'Arial', 'Apple Color Emoji', 'Segoe UI Emoji'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(110,68,255,.08), 0 10px 40px rgba(110,68,255,.25)'
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' }
        },
        pulseRing: {
          '0%': { transform: 'scale(.9)', opacity: '.7' },
          '80%, 100%': { transform: 'scale(1.3)', opacity: '0' }
        },
        spinSlow: {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' }
        }
      },
      animation: {
        pulse: 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        float: 'float 8s ease-in-out infinite',
        pulseRing: 'pulseRing 2.4s cubic-bezier(0.215, 0.61, 0.355, 1) infinite',
        spinSlow: 'spinSlow 32s linear infinite',
        shimmer: 'shimmer 2.5s linear infinite',
        fadeIn: 'fadeIn 0.5s ease-out',
        slideIn: 'slideIn 0.6s ease-out'
      },
      backgroundImage: {
        grid: 'radial-gradient(transparent 1px, rgba(255,255,255,0.04) 1px)',
      }
    },
  },
  plugins: [],
}

