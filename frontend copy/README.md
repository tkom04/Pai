# Personal AI Frontend

A modern Next.js frontend for the Personal AI Dashboard, featuring real-time integration with calendar, tasks, smart home, budget tracking, and AI chat capabilities.

## 🚀 Features

- **📅 Calendar Integration** - View and manage Google Calendar events
- **✅ Task Management** - Notion-powered task tracking with status updates
- **🏠 Smart Home Control** - Home Assistant device management
- **💰 Budget Tracking** - Financial transaction management and insights
- **🤖 AI Chat** - Interactive AI assistant for all your needs
- **🔐 Secure Authentication** - Supabase-powered user authentication
- **📱 Responsive Design** - Mobile-first approach with Tailwind CSS

## 🛠️ Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Supabase** - Authentication and database
- **Axios** - HTTP client for API communication

## 📦 Installation

1. **Clone and navigate to the frontend directory:**
   ```bash
   cd personal-ai/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env.local
   ```

   Edit `.env.local` with your configuration:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
   NEXT_PUBLIC_API_URL=http://localhost:8080
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🏗️ Project Structure

```
frontend/
├── components/           # React components
│   ├── AuthProvider.tsx  # Authentication context
│   ├── ProtectedRoute.tsx # Route protection
│   ├── Dashboard.tsx     # Main dashboard layout
│   ├── AiChat.tsx        # AI chat interface
│   ├── CalendarView.tsx  # Calendar management
│   ├── TasksView.tsx     # Task management
│   ├── HomeAssistantView.tsx # Smart home control
│   └── BudgetView.tsx    # Budget tracking
├── lib/                  # Utility libraries
│   ├── supabase.ts       # Supabase client
│   ├── api.ts           # API client configuration
│   └── errorHandler.ts  # Error handling utilities
├── pages/               # Next.js pages
│   ├── _app.tsx         # App wrapper
│   ├── index.tsx        # Home page (redirects)
│   ├── login.tsx        # Authentication page
│   └── dashboard.tsx    # Main dashboard
├── styles/              # Global styles
│   └── globals.css      # Tailwind CSS imports
└── public/              # Static assets
```

## 🔧 Configuration

### Supabase Setup
1. Create a new project at [supabase.com](https://supabase.com)
2. Get your project URL and anon key from Settings > API
3. Add them to your `.env.local` file

### Backend Integration
Make sure your Personal AI backend is running on `http://localhost:8080` (or update `NEXT_PUBLIC_API_URL` in your environment file).

## 📱 Usage

### Authentication
- **Sign Up**: Create a new account with email/password
- **Sign In**: Use your existing credentials
- **Auto-redirect**: Logged-in users are automatically redirected to the dashboard

### Dashboard Navigation
- **📅 Calendar**: View upcoming events, add new events
- **✅ Tasks**: Manage Notion tasks, update status, set priorities
- **🏠 Home**: Control smart home devices, view sensor data
- **💰 Budget**: Track income/expenses, view financial insights
- **🤖 AI Chat**: Interact with your AI assistant

### Features
- **Morning Brief**: Get a daily summary of your schedule and tasks
- **Real-time Updates**: Device states and data refresh automatically
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Error Handling**: Graceful error messages and loading states

## 🚀 Deployment

### Vercel (Recommended)
1. Push your code to GitHub
2. Connect your repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy!

### Other Platforms
The app can be deployed to any platform that supports Next.js:
- Netlify
- AWS Amplify
- Railway
- DigitalOcean App Platform

## 🔒 Security

- **Authentication**: Secure user authentication via Supabase
- **Protected Routes**: Dashboard requires authentication
- **API Security**: Requests include authentication tokens
- **Environment Variables**: Sensitive data stored securely

## 🐛 Troubleshooting

### Common Issues

1. **Authentication not working**
   - Check Supabase URL and keys in `.env.local`
   - Ensure Supabase project is active

2. **API calls failing**
   - Verify backend is running on correct port
   - Check `NEXT_PUBLIC_API_URL` in environment

3. **Styling issues**
   - Ensure Tailwind CSS is properly configured
   - Check `globals.css` imports

### Development Tips

- Use browser dev tools to inspect API calls
- Check console for error messages
- Verify environment variables are loaded correctly

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the Personal AI system. See the main project for licensing information.

---

**Need help?** Check the main Personal AI documentation or open an issue in the repository.
