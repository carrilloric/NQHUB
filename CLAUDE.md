# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NQHUB is a professional trading analytics platform for NQ Futures (Nasdaq 100 E-mini Futures) built as a full-stack React application with FastAPI backend. The platform features:
- Data ingestion and ETL pipeline monitoring
- Real-time charting and visualization
- **ICT Pattern Detection** (Fair Value Gaps, Liquidity Pools, Order Blocks)
- Statistical analysis (EDA, unsupervised learning, regression)
- Backtesting (rule-based and AI-powered)
- AI-powered chat assistant

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
│   ├── DataModule.tsx          # Data Module (3 tabs: Ingest, Charts, Pattern Detection)
│   ├── StatisticalAnalysis.tsx # Statistical Analysis (3 tabs: EDA, Unsupervised, Regression)
│   └── ...
├── components/
│   ├── ui/                     # Radix-based reusable UI components
│   ├── layout/                 # TopNavbar, Sidebar
│   ├── data-module/            # Data Module specific components
│   │   ├── charts/             # Chart components
│   │   ├── etl/                # ETL dashboard components
│   │   └── patterns/           # Pattern detection UI (FVG, LP, OB)
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
- `/data` - Data Module with 3 tabs (Ingest, Charts, Pattern Detection)
- `/data/charts` - Direct link to charts tab (legacy route, use tabs instead)
- `/statistical-analysis` - Statistical Analysis with 3 tabs (EDA, Unsupervised Learning, Regression)
- `/backtesting/rule-based` - Rule-Based Backtesting Module (placeholder)
- `/backtesting/ai` - AI-Powered Backtesting Module (placeholder)
- `/bot` - BOT Module (placeholder, traders/admins only)

**Authentication**: Role-based access control with roles: `admin`, `trader`, `analystSenior`, `analystJunior`.

### API Integration

**Development**: Single port (8080) serves both frontend and backend via Vite plugin that integrates Express.

**API Routes**: All API endpoints are prefixed with `/api/` and defined in `server/index.ts`.

**Mock Data System**: All mock data functions are in `shared/mock-data.ts` with clear comments showing which API endpoint should replace them. See `SCICHART_SETUP.md` for replacement guide.

## Data Module Architecture

The Data Module (`/data`) is the core analytics interface with **three main tabs**:

### 1. Data Ingest & ETL
Upload and process market data with ETL pipeline monitoring:
- **File Upload**: Drag-and-drop CSV/ZIP upload with validation
- **ETL Jobs**: Real-time job monitoring with status tracking
- **Coverage Heatmap**: Visual representation of data coverage across timeframes
- **Database Stats**: Candle counts, tick counts, active contracts
- **Integrity Checks**: Data validation and gap detection

**Components**: `DataIngestETLSection.tsx`, `ETLDashboard.tsx`, `FileUploader.tsx`, `JobMonitor.tsx`, `CoverageHeatMap.tsx`

### 2. Charts
Multi-chart view with indicators and analysis tools:
- **MultiChartView**: Flexible grid layouts (2x2, 3x1, 4x1, custom)
- **Chart Types**: Candlestick, footprint, volume profile (SciChart integration ready)
- **Indicators**: Pre-defined by category (Volume, Momentum, Trend, Volatility, Orderflow)
- **Detachable Windows**: Charts can be detached to separate windows

**Pre-defined indicators by category**:
- **Volume**: Volume, OBV, VPT
- **Momentum**: RSI, MACD, Stochastic
- **Trend**: SMA, EMA, ADX
- **Volatility**: Bollinger Bands, ATR
- **Orderflow**: Delta, CVD

**Components**: `ChartsSection.tsx`, `ProfessionalChart/`, `IndicatorLibrary.tsx`

### 3. Pattern Detection (ICT)
Automated detection of Inner Circle Trader (ICT) patterns:
- **Fair Value Gaps (FVG)**: Price gaps with ICT-specific fields
- **Liquidity Pools (LP)**: EQH/EQL clusters, session levels (NYH, NYL, ASH, ASL, etc.)
- **Order Blocks (OB)**: Last candle before impulse move with quality classification

**Components**: `PatternDetectionSection.tsx`, `patterns/FVGGenerator.tsx`, `patterns/LPGenerator.tsx`, `patterns/OBGenerator.tsx`

**See**: `docs/PATTERN_DETECTION_GUIDE.md` for complete pattern detection documentation.

**Note**: The Data Module appears as a single entry in the sidebar but contains 3 internal tabs for navigation.

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

### Timezone Handling (CRITICAL)

⚠️ **All timestamps MUST be stored as UTC naive in PostgreSQL.**

**The Problem**: SQL queries with `AT TIME ZONE 'America/New_York'` return naive datetimes in ET, but PostgreSQL interprets them as UTC when saving. This causes 5-hour timezone offset errors.

**The Correct Pattern** (copy from FVG detector):

```python
import pytz

eastern = pytz.timezone('America/New_York')

# Step 1: Localize naive ET datetime to ET aware
formation_time_aware = eastern.localize(row.et_time)

# Step 2: Convert to UTC aware
formation_time_utc = formation_time_aware.astimezone(pytz.UTC)

# Step 3: Remove timezone info for DB storage
formation_time_utc_naive = formation_time_utc.replace(tzinfo=None)

# Step 4: Save to database
pattern = DetectedPattern(
    formation_time=formation_time_utc_naive  # ← UTC naive
)
```

**Display Format**: Text reports MUST show `"YYYY-MM-DD HH:MM:SS EST (HH:MM:SS UTC)"`

**See**: `docs/TIMEZONE_HANDLING.md` for complete guide, validation checklist, and troubleshooting.

### Server Time System

NQHUB maintains a centralized server time system that provides a single source of truth for date/time across the application.

**Key Features:**
- Server time maintained in Eastern Time (ET) with automatic DST handling
- Real-time clock display in TopNavbar
- Automatic sync every 60 seconds
- Connection status indicators (green/yellow/red)
- Available globally via `useServerTime()` hook

**Usage:**
```typescript
import { useServerTime } from '@/state/server-time';

const { getCurrentTime, getFormattedET } = useServerTime();
// Returns: "2024-11-29 14:30:45 ET (19:30:45 UTC)"
```

**Endpoints:**
- `GET /api/v1/system/time` - Get current server time
- `GET /api/v1/system/config` - Get timezone configuration
- `GET /api/v1/system/heartbeat` - Connection check

**See**: `docs/SERVER_TIME_IMPLEMENTATION.md` for complete implementation details.

### Internationalization

i18n files in `client/locales/` (en.json, es.json). Access translations via:

```typescript
import { useI18n } from '@/state/app';
const { t } = useI18n();
```

## Pattern Detection System (ICT)

NQHUB implements automated detection of Inner Circle Trader (ICT) patterns based on price action analysis. All patterns are stored in PostgreSQL with TimescaleDB for efficient time-series queries.

### Backend Architecture

**Location**: `backend/app/services/pattern_detection/`

**Pattern Detectors**:
- `fvg_detector.py` - Fair Value Gaps detection
- `lp_detector.py` - Liquidity Pools detection
- `ob_detector.py` - Order Blocks detection

**Database Models**: `backend/app/models/patterns.py`
- `DetectedFVG` - Fair Value Gap records
- `DetectedLiquidityPool` - Liquidity Pool records
- `DetectedOrderBlock` - Order Block records
- `PatternInteraction` - Pattern interaction tracking (R0-R4, P1-P5)

**API Endpoints**: `backend/app/api/v1/endpoints/patterns.py`
- `POST /api/v1/patterns/fvgs/generate` - Generate FVGs for date range
- `POST /api/v1/patterns/liquidity-pools/generate` - Generate LPs for date
- `POST /api/v1/patterns/order-blocks/generate` - Generate OBs for date range
- `GET /api/v1/patterns/fvgs` - List FVGs with filters
- `GET /api/v1/patterns/liquidity-pools` - List LPs with filters
- `GET /api/v1/patterns/order-blocks` - List OBs with filters

### Pattern Types

#### 1. Fair Value Gaps (FVG)
Price gaps created by imbalance between buyers and sellers.

**Detection Criteria** (see `docs/FVG_CRITERIOS_DETECCION.md`):
- 3-candle pattern with non-overlapping wicks
- Minimum gap size (auto-calculated from ATR)
- Significance levels: MICRO, SMALL, MEDIUM, LARGE, EXTREME

**ICT-Specific Fields**:
- `premium_level`: High boundary (resistance)
- `discount_level`: Low boundary (support)
- `consequent_encroachment`: 50% level (most important retracement target)
- `displacement_score`: Energetic movement score
- `has_break_of_structure`: BOS detection flag

**States**: UNMITIGATED, REDELIVERED, REBALANCED

**Docs**: `docs/FVG_TEORIA_ICT.md`, `docs/DETECCION_FAIR_VALUE_GAPS.md`

#### 2. Liquidity Pools (LP)
Areas where stop-loss orders accumulate, creating liquidity.

**Pool Types**:
- **EQH/EQL**: Equal highs/lows (2+ touches within tolerance)
- **Session Levels**: NYH, NYL, ASH, ASL, LSH, LSL
- **Swing Levels**: SWING_HIGH, SWING_LOW (pending)

**Detection Criteria** (see `docs/LIQUIDITY_POOLS_CRITERIOS.md`):
- Tolerance: Auto-calculated from ATR (default 10 points)
- Minimum touches: 2 for EQH/EQL
- Rectangle representation: zone_low, zone_high, start_time, end_time

**ICT Lifecycle**:
- Modal level: Price level with most touches
- Sweep detection: 3 criteria (penetration, volume, reversal)
- States: UNMITIGATED, RESPECTED, SWEPT, MITIGATED

**Docs**: `docs/LIQUIDITY_POOL_STATES.md`, `docs/LP_20NOV_CRITICAL_LEVELS.md`

#### 3. Order Blocks (OB)
Last candle before significant impulse move, represents institutional order placement.

**Detection Criteria** (see `docs/ORDER_BLOCKS_CRITERIOS.md`):
- Minimum impulse: Auto-calculated from ATR (2.5x typical move)
- Strong threshold: 1.5x minimum impulse
- Classification: BULLISH OB, BEARISH OB, STRONG BULLISH OB, STRONG BEARISH OB

**Quality Levels**:
- HIGH: Strong impulse + large volume + tight range
- MEDIUM: Moderate impulse
- LOW: Minimum impulse threshold

**Key Fields**:
- `ob_body_midpoint`: 50% of candle body = (open + close) / 2
- `ob_range_midpoint`: 50% of candle range = (high + low) / 2
- `impulse_move`: Size of impulse in points
- `impulse_direction`: UP or DOWN

**States**: ACTIVE, TESTED, BROKEN

**Docs**: `docs/OB_24NOV_SAMPLE.md`, `docs/REBOTE_Y_PENETRACION_CRITERIOS.md`

### Pattern Interactions

**Location**: `backend/app/services/pattern_detection/interaction_detector.py` (pending)

**Interaction Types** (see `docs/REBOTE_Y_PENETRACION_CRITERIOS.md`):
- **R0**: Clean bounce (0% penetration)
- **R1**: Shallow touch (0.1-10% penetration)
- **R2**: Moderate retest (10-25% penetration)
- **R3**: Deep retest (25-50% penetration)
- **R4**: Full retest (50-90% penetration)
- **P1-P5**: Penetration levels (breakout scenarios)

### Frontend Integration

**Pattern Detection Section**: `frontend/src/client/components/data-module/PatternDetectionSection.tsx`

**Pattern Generators**:
- `patterns/FVGGenerator.tsx` - FVG generation UI
- `patterns/LPGenerator.tsx` - LP generation UI
- `patterns/OBGenerator.tsx` - OB generation UI

**Features**:
- Date range selection with calendar picker
- Real-time generation with progress tracking
- Markdown-formatted reports with statistics
- List view with filters (status, quality, significance)
- Auto-parameter display (min_gap_size, tolerance, min_impulse)

## Statistical Analysis Module

The Statistical Analysis Module (`/statistical-analysis`) is an independent section for advanced data analysis with three main tabs.

**Location**: `frontend/src/client/pages/StatisticalAnalysis.tsx`

### 1. Exploratory Data Analysis (EDA)
Investigate feature behavior and distributional properties before modeling.

**Features**:
- **Univariate analysis**: Summary statistics, density plots, extreme value detection
- **Bivariate relationships**: Scatter matrices, rank correlations
- **Correlation analysis**: Clustered heatmaps, Pearson/Spearman coefficients, multicollinearity detection
- **Distribution assessment**: Normality tests (Shapiro-Wilk, Anderson-Darling), stationarity tests (ADF)

### 2. Unsupervised Learning Analysis
Reveal latent structure across the feature space with clustering and dimensionality reduction.

**Features**:
- **K-means clustering**: Elbow method, silhouette analysis, cluster profiling
- **Principal Component Analysis (PCA)**: Variance explained, component loadings, dimensionality reduction
- **Cluster interpretation**: Centroid analysis, representative samples

### 3. Linear Regression Modeling
Fit baseline predictive models and validate performance prior to advanced experimentation.

**Features**:
- **Simple linear regression**: Univariate models, confidence intervals, R² metrics
- **Multiple linear regression**: Multivariate fits, regularization (Ridge/Lasso), cross-validation
- **Model diagnostics**: Residual analysis, leverage detection, heteroscedasticity tests (Breusch-Pagan, White)
- **Interpretation**: Coefficient insights, RMSE/MAE/R² on test set, production readiness assessment

**Status**: UI implemented, backend analysis pending

## Backtesting Modules

NQHUB features two separate backtesting approaches for strategy testing and optimization.

### 1. Rule-Based Backtesting (`/backtesting/rule-based`)
Traditional algorithmic strategy testing with predefined rules and parameters.

**Planned Features**:
- Strategy builder with visual rule configuration
- Historical data replay with pattern overlay
- Performance metrics (Sharpe ratio, max drawdown, win rate)
- Optimization grid search
- Walk-forward validation

**Status**: Placeholder (route defined, implementation pending)

### 2. AI-Powered Backtesting (`/backtesting/ai`)
Machine learning-driven strategy optimization using pattern detection and market structure analysis.

**Planned Features**:
- Automated feature engineering from detected patterns
- Reinforcement learning for strategy optimization
- Neural network-based entry/exit prediction
- Ensemble model comparison
- AutoML integration

**Status**: Placeholder (route defined, implementation pending)

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

### Core Documentation
- `AGENTS.md` - Project overview and tech stack summary
- `DATA_MODULE_STRUCTURE.md` - Detailed data module architecture
- `SCICHART_SETUP.md` - Guide for replacing mock data with real API and SciChart integration
- `docs/DATA_DICTIONARY.md` - **CRITICAL** Complete metadata catalog of all database fields with format specifications, formulas, and business rules

### Pattern Detection (ICT)
- `docs/PATTERN_DETECTION_GUIDE.md` - Complete pattern detection system guide
- `docs/FVG_TEORIA_ICT.md` - Fair Value Gap theory and ICT concepts
- `docs/FVG_CRITERIOS_DETECCION.md` - FVG detection criteria and parameters
- `docs/DETECCION_FAIR_VALUE_GAPS.md` - FVG implementation details
- `docs/ORDER_BLOCKS_CRITERIOS.md` - Order Block detection criteria
- `docs/LIQUIDITY_POOLS_CRITERIOS.md` - Liquidity Pool detection criteria
- `docs/LIQUIDITY_POOL_STATES.md` - LP lifecycle and state management
- `docs/REBOTE_Y_PENETRACION_CRITERIOS.md` - Pattern interaction classification (R0-R4, P1-P5)

### Critical References
- `docs/TIMEZONE_HANDLING.md` - **CRITICAL** timezone handling best practices and validation checklist
- `docs/SIDEBAR_NAVIGATION.md` - Sidebar navigation structure and adding new sections
- `docs/DATABASE_SCHEMA.md` - Complete database schema including pattern detection tables
