# NQHUB Frontend

React 18 + TypeScript + Vite frontend for NQHUB Trading Analytics Platform.

## Tech Stack

- **React** 18.3.1
- **TypeScript** 5.9.2
- **Vite** 7.1.2 (build tool)
- **React Router** 6.30.1
- **TailwindCSS** 3.4.17
- **Radix UI** (UI components)
- **Zustand** 5.0.8 (business state)
- **React Context** (infrastructure state)
- **TanStack Query** 5.84.2
- **SciChart** (trial mode)

## Project Structure

```
src/
├── client/
│   ├── pages/              # Route components
│   ├── components/
│   │   ├── ui/            # Radix-based components
│   │   ├── layout/        # TopNavbar, Sidebar
│   │   ├── data-module/   # Data analytics
│   │   ├── ai-assistant/  # AI chat (to implement)
│   │   ├── admin/         # Admin panel (to implement)
│   │   ├── auth/          # Auth components (to implement)
│   │   └── common/        # Shared components
│   ├── state/
│   │   ├── app.tsx        # Global state (Context)
│   │   └── data-module.store.ts  # Data module (Zustand)
│   ├── services/          # API clients (to implement)
│   ├── lib/               # Utilities
│   ├── locales/           # i18n (en, es)
│   ├── App.tsx            # App entry + routing
│   └── global.css         # TailwindCSS globals
└── shared/                # Shared with backend
    ├── api.ts             # Type definitions
    └── mock-data.ts       # Mock data (to replace)
```

## Development

### Install dependencies
```bash
pnpm install
```

### Start dev server
```bash
pnpm dev
```

Frontend runs on **port 3000** with proxy to backend on port 8000.

### Build for production
```bash
pnpm build
```

### Run tests
```bash
pnpm test
```

### Type checking
```bash
pnpm typecheck
```

### Format code
```bash
pnpm format.fix
```

## Configuration

### Environment Variables

Create `.env` file:
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENVIRONMENT=development
```

### Vite Configuration

- Port: 3000
- Proxy: `/api` → `http://localhost:8000`
- WebSocket proxy: `/ws` → `ws://localhost:8000`
- Aliases: `@/` → `src/client/`, `@shared/` → `src/shared/`

## State Management

### Zustand (Business Logic)
Used for frequently changing domain state:
- Chart data and management
- Indicators
- Layouts
- Real-time data

Example:
```typescript
import { useDataModuleStore } from '@/state/data-module.store';

const { charts, addChart } = useDataModuleStore();
```

### React Context (Infrastructure)
Used for app-wide, infrequently changing state:
- Authentication
- UI configuration (theme, language)
- API client instances

Example:
```typescript
import { useAuth, useUI } from '@/state/app';

const { user, isAuthenticated } = useAuth();
const { theme, setTheme } = useUI();
```

## Routing

Routes are defined in `App.tsx` using React Router 6.

Protected routes wrap in `<ProtectedRoute>`:
```typescript
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

## Styling

- **Primary**: TailwindCSS utility classes
- **Theme**: Configured in `global.css` and `tailwind.config.ts`
- **Components**: Pre-built Radix UI components in `components/ui/`
- **Utility**: `cn()` from `lib/utils.ts` for conditional classes

## Internationalization

i18n support with English and Spanish:
```typescript
import { useI18n } from '@/state/app';

const { t } = useI18n();
const text = t('key.in.locale.json');
```

## API Integration

APIs will be accessed via services (to implement):
```typescript
// src/client/services/api-client.ts
import { apiClient } from '@/services/api-client';

const response = await apiClient.get('/api/charts/candles');
```

## Key Features

### Current
- ✅ Component library (Radix UI)
- ✅ State management setup
- ✅ Routing with protection
- ✅ i18n support
- ✅ Mock data for development

### In Development
- 🚧 Authentication UI
- 🚧 Admin panel
- 🚧 AI Assistant chat
- 🚧 API client with JWT
- 🚧 WebSocket client
- 🚧 Real data integration

### Planned
- 📋 SciChart integration
- 📋 Voice controls (ElevenLabs)
- 📋 Advanced charting features
- 📋 Real-time data updates

## Building for Production

```bash
pnpm build
```

Output in `dist/` directory. Can be served with any static file server or containerized with the provided Dockerfile.

## Docker

```bash
# From project root
docker build -f docker/Dockerfile.frontend -t nqhub-frontend .
docker run -p 80:80 nqhub-frontend
```

## Notes

- SciChart is in **trial mode** - production license required
- Mock data in `src/shared/mock-data.ts` will be replaced with real API calls
- TypeScript **strict mode is disabled** for flexibility during development
