# 🎉 Orbit Landing Page Onboarding Setup

Your new landing page has been successfully integrated! Here's what you need to do to complete the setup.

## 📋 What Was Changed

### 1. ✅ New Landing Page (V2 with Solar System!)
- **File**: `pwa/pages/index.tsx`
- Replaced the old home page with a beautiful onboarding/marketing landing page
- Features:
  - Hero section with **toggleable orbital animation**:
    - **Stylized orbit**: Abstract animated orbits
    - **Solar system mode**: Real planetary positions based on actual orbital mechanics! 🪐
  - "How it works" section
  - Benefits section
  - Integrations showcase
  - Waitlist form with Supabase integration
  - FAQ section
  - Responsive design with animations
  - Interactive toggle to switch between stylized and accurate solar system visualization

### 2. ✅ Tailwind Configuration Updated
- **File**: `pwa/tailwind.config.js`
- Added custom colors: `violet`, `midnight`, `snow`, `ink`
- Added animations: `float`, `pulseRing`, `spinSlow`, `shimmer`, `fadeIn`, `slideIn`
- Added custom shadows: `glow`

### 3. ✅ Global Styles Updated
- **File**: `pwa/styles/globals.css`
- Added smooth scrolling for anchor links

### 4. ✅ Supabase Migration Created
- **File**: `supabase_migrations/004_waitlist.sql`
- Creates `waitlist` table to store signup emails

## 🚀 Setup Instructions

### Step 1: Apply the Database Migration

Run the migration to create the waitlist table in your Supabase database:

```bash
# Using Supabase CLI (recommended)
supabase db push

# OR manually execute the SQL
# Copy the contents of supabase_migrations/004_waitlist.sql
# and run it in your Supabase SQL editor
```

### Step 2: Restart Your Development Server

```bash
cd pwa
npm run dev
```

### Step 3: Test the Landing Page

1. Visit http://localhost:3000
2. You should see the new Orbit landing page
3. Test the waitlist form:
   - Fill in first name, email, and role
   - Click "Join the waitlist"
   - Should see success message

### Step 4: Verify Database

Check your Supabase dashboard → Table Editor → `waitlist` to see submitted entries.

## 🔧 Configuration Options

### Change Demo Video

In `pwa/pages/index.tsx`, look for this section (around line 512):

```tsx
<div className="w-full aspect-video rounded-xl bg-white/[0.06] grid place-items-center text-white/60 text-sm">
  (Embed your Loom/YouTube here)
</div>
```

Replace with:

```tsx
<iframe
  className="w-full aspect-video rounded-xl"
  src="https://www.youtube.com/embed/YOUR_VIDEO_ID"
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowFullScreen
></iframe>
```

### Customize Navigation Links

The landing page has navigation links to:
- Login page: `/login` (top right "Sign In" button)
- Dashboard: Referenced in content but not directly linked

If you need to adjust these, search for `/login` and `/dashboard` in `pwa/pages/index.tsx`.

### Customize Colors

All colors are defined in `pwa/tailwind.config.js`:
- `violet`: Main brand color (#6E44FF)
- `midnight`: Background color (#0B0B10)
- Adjust these to match your brand

## 📁 File Structure

```
pwa/
├── pages/
│   ├── index.tsx          ← New onboarding landing page
│   ├── dashboard.tsx      ← Main app dashboard (unchanged)
│   ├── login.tsx          ← Login page (unchanged)
│   └── ...
├── styles/
│   └── globals.css        ← Updated with smooth scroll
├── tailwind.config.js     ← Updated with custom theme
└── ...

supabase_migrations/
└── 004_waitlist.sql       ← New waitlist table migration
```

## 🎨 Design Features

- **Animations**: Smooth float, pulse, and spin animations
- **Responsive**: Mobile-first design that scales beautifully
- **Dark Theme**: Midnight background with violet accents
- **Glass Morphism**: Subtle transparency effects
- **Smooth Scrolling**: Anchor links scroll smoothly to sections
- **🪐 Solar System Toggle**: Interactive visualization showing:
  - **Stylized mode**: Clean, abstract orbits with smooth animations
  - **Solar system mode**: Accurate planetary positions using heliocentric orbital mechanics (updates every minute to reflect real-time positions relative to J2000 epoch)

## 🔐 Security Notes

The waitlist table has Row Level Security (RLS) enabled:
- **Public**: Can INSERT (sign up)
- **Authenticated users**: Can SELECT and UPDATE (view/manage waitlist)
- No one can delete entries (data safety)

## 🐛 Troubleshooting

### "Cannot find module '@/lib/supabase'"

Make sure you have the Supabase client configured in your project. If not, you'll need to:

1. Install Supabase client:
```bash
npm install @supabase/supabase-js
```

2. Create `pwa/lib/supabase.ts`:
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const getSupabaseClient = () => {
  return createClient(supabaseUrl, supabaseAnonKey)
}
```

3. Add to `.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### Waitlist Form Not Working

1. Check browser console for errors
2. Verify Supabase credentials in `.env.local`
3. Confirm migration was applied successfully
4. Check Supabase logs for errors

## 📊 Analytics (Optional)

To track waitlist signups, add analytics to the `handleSubmit` function in `index.tsx`:

```typescript
// After successful signup
if (typeof gtag !== 'undefined') {
  gtag('event', 'waitlist_signup', {
    'event_category': 'engagement',
    'event_label': formData.role
  });
}
```

## 🎯 Next Steps

1. ✅ Apply database migration
2. ✅ Test the landing page
3. ✅ Add your demo video
4. 🔄 Customize copy/content as needed
5. 🔄 Add analytics tracking
6. 🔄 Configure email notifications for new signups (optional)

---

**Questions?** The landing page is fully functional and ready to go! Just apply the migration and restart your dev server.

