# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NQHUB is a professional trading analytics platform for NQ Futures (Nasdaq 100 E-mini Futures) built as a full-stack React application with FastAPI backend. The platform features data ingestion, charting/visualization, ETL pipeline monitoring, and an AI-powered chat assistant.

## Development Environment

### Service Ports
- **Frontend (Vite)**: http://localhost:3001
- **Backend (FastAPI)**: http://localhost:8002
  - API Docs: http://localhost:8002/api/docs
  - Redoc: http://localhost:8002/api/redoc
- **PostgreSQL + TimescaleDB**: localhost:5433
  - Docker container: `nqhub_postgres`
  - User: `nqhub` / Password: `nqhub_password`
  - Database: `nqhub`
- **Mailpit (email testing)**: http://localhost:8025
- **Neo4j Browser**: http://localhost:7474 (planned)
- **RedisInsight**: http://localhost:8001 (planned)

**Important:** Port 5432 is reserved for legacy `nq_orderflow` database in another WSL instance.

### Docker Containers

```bash
# Check running containers
docker ps

# PostgreSQL/TimescaleDB (always use port 5433)
docker start nqhub_postgres
docker stop nqhub_postgres

# Restart if needed
docker restart nqhub_postgres
```

## Technology Stack

- **Package Manager**: pnpm (frontend), pip (backend)
- **Frontend**: React 18 + React Router 6 SPA + TypeScript + Vite + TailwindCSS 3
- **Backend**: FastAPI (Python 3.11+) + PostgreSQL + TimescaleDB
- **State Management**: Zustand for data module state, React Context for app-wide state
- **UI Components**: Radix UI + custom components in `client/components/ui/`
- **Testing**: Playwright (E2E), Vitest (unit tests)
- **Charting**: Prepared for SciChart integration (not yet installed)

## Development Commands

### Frontend (from /frontend)
```bash
pnpm dev              # Start Vite dev server on http://localhost:3001
pnpm build            # Build for production
pnpm test             # Run Vitest tests
pnpm test:e2e         # Run Playwright E2E tests
pnpm typecheck        # TypeScript validation
```

### Backend (from /backend)
```bash
source .venv/bin/activate              # Activate virtual environment
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002  # Start FastAPI server
alembic upgrade head                   # Run database migrations
pytest                                 # Run backend tests
```

## Project Architecture

### Directory Structure

```
client/                          # React SPA frontend
├── pages/                       # Route components
│   ├── Index.tsx               # Landing page (unauthenticated)
│   ├── Dashboard.tsx           # Main dashboard (authenticated)
│   ├── DataModule.tsx          # Data analytics main page
│   └── ...
├── components/
│   ├── ui/                     # Radix-based reusable UI components
│   ├── layout/                 # TopNavbar, Sidebar
│   ├── data-module/            # Data Module specific components
│   │   ├── charts/             # Chart components (CandlestickChart, MultiChartView)
│   │   ├── indicators/         # Indicator management UI
│   │   └── etl/                # ETL dashboard components
│   └── common/                 # Shared components
├── state/
│   ├── app.tsx                 # Global app state (auth, UI, i18n)
│   └── data-module.store.ts    # Zustand store for data module
├── lib/                        # Utility functions (cn helper, etc.)
├── locales/                    # i18n JSON files (en.json, es.json)
├── App.tsx                     # App entry with routing setup
└── global.css                  # TailwindCSS theme and global styles

server/                         # Express API backend
├── index.ts                    # Main server setup and routes
├── routes/                     # API route handlers
└── node-build.ts              # Production server entry

shared/                         # Types shared between client & server
├── api.ts                      # Shared API interfaces
└── mock-data.ts               # Mock data generators (to be replaced with real API)
```

### Path Aliases

- `@/*` → `./client/*`
- `@shared/*` → `./shared/*`

## Key Architecture Patterns

### State Management Strategy

NQHUB uses a **hybrid approach** combining React Context and Zustand, each serving specific purposes:

#### React Context (`client/state/app.tsx`)
Used for **infrastructure-level state** that rarely changes:
- **Authentication**: user, login, logout, role-based access
- **UI Configuration**: sidebar collapsed, LLM panel, theme, language
- **Services/Utilities**: API client instances, i18n helpers
- **Feature Flags**: Configuration from backend

**Why Context here?**
- State changes infrequently
- Needs to be available throughout the entire app
- Ideal for "injecting" services (like API client)
- Natural fit for cross-cutting concerns

#### Zustand (`client/state/data-module.store.ts`)
Used for **business/domain state** that changes frequently:
- **Chart Management**: add, remove, update charts
- **Chart Data**: OHLCV candles, footprint data (real-time updates)
- **Timeframe Selection**: user interactions
- **Indicator Management**: add, remove, toggle visibility
- **Layout Management**: save/load chart layouts

**Why Zustand here?**
- Excellent performance with frequent updates (only re-renders affected components)
- Less boilerplate than Context
- Perfect for transactional/business logic
- Better DevTools support
- Ideal for real-time data updates

#### Recommended Pattern

```typescript
// API Service in Context (infrastructure)
const ApiContext = createContext<ApiService>(null);

// Business logic in Zustand (domain)
export const useDataModuleStore = create<DataModuleStore>((set, get) => ({
  loadCandles: async (symbol, timeframe) => {
    const api = getApiClient(); // From Context
    const data = await api.charts.getCandles({ symbol, timeframe });
    set({ ohlcvData: data });
  }
}));
```

**Rule of thumb:**
- **React Context** → Infrastructure (auth, API, config, theme)
- **Zustand** → Business Logic (trading data, charts, user actions)

### Routing & Authentication

Routing uses React Router 6 with protected routes wrapped in `<ProtectedRoute>`. Routes are defined in `client/App.tsx`.

**Key Routes**:
- `/` - Landing page (unauthenticated)
- `/dashboard` - Main dashboard
- `/data` - Data Module with tabs
- `/data/charts` - Direct link to charts tab
- `/data/analysis` - Direct link to analysis tab

**Authentication**: Currently uses mock login in `client/state/app.tsx`. Role-based access control with roles: `admin`, `trader`, `analystSenior`, `analystJunior`.

### API Integration

**Development**: Single port (8080) serves both frontend and backend via Vite plugin that integrates Express.

**API Routes**: All API endpoints are prefixed with `/api/` and defined in `server/index.ts`.

**Mock Data System**: All mock data functions are in `shared/mock-data.ts` with clear comments showing which API endpoint should replace them. See `SCICHART_SETUP.md` for replacement guide.

## Data Module Architecture

The Data Module (`/data`) is the core analytics interface with three main sections:

1. **Data Upload** - Upload and process price/news data with timeframe transformations
2. **Charts** - Multi-chart view with indicators and analysis tools
3. **ETL Pipeline** - Monitor data sources and processing jobs

### Mock Data System

All mock data functions in `shared/mock-data.ts` include comments showing the target API endpoint:

```typescript
/**
 * REPLACE: generateMockOHLCVData()
 * WITH: GET /api/chart/candles?symbol={symbol}&timeframe={timeframe}&start={date}&end={date}
 */
```

When implementing real API endpoints, replace these functions while maintaining the TypeScript interfaces.

### Chart System

- **MultiChartView**: Container supporting flexible grid layouts (2x2, 3x1, 4x1, custom)
- **CandlestickChart**: Placeholder component ready for SciChart integration
- Charts are managed via Zustand store
- Supports detaching charts to separate windows

### Indicator System

Pre-defined indicators by category:
- **Volume**: Volume, OBV, VPT
- **Momentum**: RSI, MACD, Stochastic
- **Trend**: SMA, EMA, ADX
- **Volatility**: Bollinger Bands, ATR
- **Orderflow**: Delta, CVD

Indicators are added via `IndicatorLibrary.tsx` and managed in `ActiveIndicatorsList.tsx`.

## Important Development Notes

### Server Endpoints

Only create API endpoints when strictly necessary (e.g., private keys, sensitive DB operations). Prefer client-side logic when possible.

API endpoints are registered in `server/index.ts`:

```typescript
app.get("/api/your-endpoint", handleYourRoute);
```

Create route handlers in `server/routes/` and export them.

### Adding New Routes

1. Create component in `client/pages/YourPage.tsx`
2. Add route in `client/App.tsx` **before** the catch-all `*` route
3. Wrap in `<ProtectedRoute>` if authentication required

### Styling

- Primary: TailwindCSS 3 utility classes
- Theme configuration: `client/global.css` and `tailwind.config.ts`
- Use `cn()` utility from `@/lib/utils` to combine classes with conditional logic
- Dark mode supported via theme toggle

### TypeScript Configuration

TypeScript strict mode is **disabled** for flexibility. The project uses:
- Path mappings for clean imports
- ES2020 target
- Module bundler resolution

### Internationalization

i18n files in `client/locales/` (en.json, es.json). Access translations via:

```typescript
import { useI18n } from '@/state/app';
const { t } = useI18n();
```

## SciChart Integration (Pending)

Charts are prepared for SciChart but library is not yet installed. To integrate:

1. Run `pnpm install scichart`
2. Update `CandlestickChart.tsx` to use SciChart rendering
3. Set license key if needed: `SciChartSurface.setRuntimeLicenseKey('KEY')`

See `SCICHART_SETUP.md` for detailed integration guide.

## Testing

Tests use Vitest. Run with `pnpm test`. Test files should be co-located with components or in dedicated test directories.

## Deployment

- **Standard**: `pnpm build` creates production build in `dist/`
- **Cloud**: Netlify or Vercel (configured with netlify.toml)
- **Binary**: Supports pkg for self-contained executables

## Additional Documentation

- `AGENTS.md` - Project overview and tech stack summary
- `DATA_MODULE_STRUCTURE.md` - Detailed data module architecture
- `SCICHART_SETUP.md` - Guide for replacing mock data with real API and SciChart integration
