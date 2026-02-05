# Frontend

React + TypeScript frontend for A-PAULO management system.

## Tech Stack

- **React 19** + TypeScript
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Zustand** - State management
- **Axios** - HTTP client with JWT support
- **React Hook Form** - Form handling

## Quick Start

### Prerequisites
- Node.js (v16+)
- npm

### Installation & Running

1. **Install dependencies:**
```bash
npm install
```

2. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Update `VITE_API_URL` if needed (default: `http://127.0.0.1:8000/api`)

3. **Start dev server:**
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
├── components/       # Reusable components
├── lib/              # API client configuration
├── pages/            # Page components (Login, Dashboard)
├── services/         # API services
├── stores/           # Zustand state management
└── App.tsx           # Main app component
```

## Authentication

- Uses JWT tokens (stored in localStorage)
- Protected routes require valid authentication token
- Auto-logout on token expiration with redirect to login
