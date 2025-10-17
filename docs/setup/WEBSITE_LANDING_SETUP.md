# 🌐 Orbit Marketing Website Landing Page (Port 3001)

Your **marketing website** has been updated with the beautiful V2 landing page featuring the live solar system!

## 📋 What Was Changed

### 1. ✅ Marketing Website Landing Page (V2 with Solar System!)
- **File**: `website/pages/index.tsx` ← THIS IS THE MARKETING SITE (port 3001)
- **NOT** the PWA app (pwa/pages/index.tsx) which stays on port 3000
- Features:
  - Hero section with **real-time solar system animation**:
    - **Live planetary positions** based on actual orbital mechanics! 🪐
    - All 8 planets orbiting in perfect circles at their real speeds
    - Updates every minute to reflect current astronomical positions
  - "How it works" section
  - Benefits section
  - Integrations showcase
  - Waitlist form (stores in localStorage for now)
  - FAQ section
  - Responsive design with animations

### 2. ✅ Tailwind Configuration Updated
- **File**: `website/tailwind.config.js`
- Added custom colors: `violet`, `midnight`, `snow`, `ink`
- Added animations: `float`, `pulseRing`, `spinSlow`, `shimmer`, `fadeIn`, `slideIn`
- Added custom shadows: `glow`

### 3. ✅ Global Styles Updated
- **File**: `website/styles/globals.css`
- Added smooth scrolling for anchor links

## 🚀 Setup Instructions

### Step 1: Install Dependencies (if needed)

```bash
cd website
npm install
```

### Step 2: Start the Website Development Server

```bash
cd website
npm run dev
```

This will start the **marketing website** on **http://localhost:3001**

### Step 3: Test the Landing Page

1. Visit **http://localhost:3001** (NOT 3000!)
2. You should see the new Orbit landing page with live solar system
3. Watch the planets orbit in real-time! 🪐
4. Hover over planets to see their names
5. Test the waitlist form (saves to localStorage)

## 🎯 Key Differences from PWA App

| Feature | Marketing Site (3001) | PWA App (3000) |
|---------|----------------------|----------------|
| **Purpose** | Public marketing/waitlist | Authenticated user dashboard |
| **Landing page** | V2 with solar system | User home/stats page |
| **Waitlist form** | localStorage only (for now) | N/A |
| **Navigation** | Links to features/about/FAQ | Internal app navigation |
| **Login link** | Points to localhost:3000/login | Has own login page |

## 📁 File Structure

```
website/                    ← Marketing site (port 3001)
├── pages/
│   ├── index.tsx          ← NEW V2 landing page with solar system
│   ├── features.tsx       ← (existing)
│   ├── about.tsx          ← (existing)
│   └── ...
├── styles/
│   └── globals.css        ← Updated with smooth scroll
├── tailwind.config.js     ← Updated with V2 theme
└── ...

pwa/                        ← Main PWA app (port 3000)
├── pages/
│   ├── index.tsx          ← UNCHANGED - user home page
│   ├── dashboard.tsx      ← (existing)
│   └── ...
```

## 🎨 Design Features

- **🪐 Live Solar System**: Real-time planetary positions using heliocentric orbital mechanics
  - All 8 planets at their actual current positions
  - Perfect circular orbits (no weird perspective distortion)
  - Updates every minute to stay astronomically accurate
  - Hover over planets to see their names
- **Animations**: Smooth orbital motion based on real planetary speeds
- **Responsive**: Mobile-first design that scales beautifully
- **Dark Theme**: Midnight background with violet accents
- **Starfield Background**: Subtle animated starfield effect
- **Smooth Scrolling**: Anchor links scroll smoothly to sections

## 🔧 Configuration Options

### Connect Waitlist to Backend

Currently the form just saves to localStorage. To connect to your Supabase:

1. Install Supabase client in website folder:
```bash
cd website
npm install @supabase/supabase-js
```

2. Create `website/lib/supabase.ts`:
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const getSupabaseClient = () => {
  return createClient(supabaseUrl, supabaseAnonKey)
}
```

3. Update the handleSubmit function in `website/pages/index.tsx` to use Supabase (same code as in the setup guide)

### Change Demo Video

In `website/pages/index.tsx`, replace the placeholder with your video embed.

### Update Navigation Links

The "Sign In" button currently points to `http://localhost:3000/login`. Update this to your production URL when deploying.

## 🚀 Running Both Sites

You can run both simultaneously:

```bash
# Terminal 1 - PWA App (port 3000)
cd pwa
npm run dev

# Terminal 2 - Marketing Site (port 3001)
cd website
npm run dev
```

- **http://localhost:3000** → Main PWA app for logged-in users
- **http://localhost:3001** → Marketing/onboarding landing page

## 📊 Current Setup

✅ **Marketing Website**: V2 landing page with solar system
✅ **PWA App**: Original user dashboard (unchanged)
✅ **Supabase**: Waitlist table ready (apply migration if needed)
✅ **Styling**: Custom Orbit theme with animations

---

**All set!** Your marketing site is now ready with the gorgeous solar system visualization. Just start the dev server and visit port 3001! 🚀🪐

