# Frontend

React + TypeScript frontend for A-PAULO management system.

## Tech Stack

- **React 19** + TypeScript
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router v7** - Routing
- **Zustand** - State management
- **TanStack React Query** - Server state management
- **Axios** - HTTP client
- **React Hook Form** - Form handling

## Quick Start

### Prerequisites
- Node.js 16+
- npm

### Installation & Running

1. **Install dependencies:**
```bash
npm install
```

2. **Configure environment:**
   - Copy `.env.example` to `.env` (or create new)
   - Set `VITE_API_URL` (default: `http://127.0.0.1:8000/api`)

3. **Start development server:**
```bash
npm run dev
```
   - Open http://localhost:5173

### Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run lint     # Run ESLint
npm run preview  # Preview production build
```

## Project Structure

```
src/
├── components/
│   └── ProtectedRoute.tsx    # Route protection wrapper
├── lib/
│   └── api.ts                # Axios API client with interceptors
├── pages/
│   ├── DashboardPage.tsx     # Main dashboard
│   └── LoginPage.tsx         # Login page
├── services/
│   └── authService.ts        # Authentication API calls
├── stores/
│   └── authStore.ts          # Auth state (Zustand)
├── App.tsx                   # Main app with routing
├── App.css                   # Component styles
├── main.tsx                  # React entry point
└── index.css                 # Global styles + Tailwind
```

## Authentication & Security

- JWT-based authentication (access + refresh tokens)
- Tokens stored in localStorage
- Protected routes using `ProtectedRoute` component
- Automatic token refresh on expiration
- Axios interceptors for attaching Bearer tokens
- Auto-redirect to login when unauthorized
