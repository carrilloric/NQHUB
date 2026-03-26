# Data Module Architecture

## Overview

The Data Module is structured as a professional trading analytics platform with three main sections:

1. **Data Upload** - File upload and processing
2. **Charts** - Data visualization and analysis
3. **ETL Pipeline** - Data source monitoring

## Directory Structure

```
client/
├── components/data-module/
│   ├── charts/
│   │   ├── CandlestickChart.tsx          # Main candlestick visualization
│   │   ├── MultiChartView.tsx            # Multi-chart container with grid
│   │   └── (Coming: FootprintChart, VolumeProfilePanel, etc.)
│   ├── indicators/
│   │   ├── IndicatorLibrary.tsx          # Browse and add indicators
│   │   ├── ActiveIndicatorsList.tsx      # Manage active indicators
│   │   └── IndicatorConfigPanel.tsx      # TODO: Parameter configuration
│   ├── etl/
│   │   ├── ETLDashboard.tsx              # Pipeline monitoring
│   │   ├── DataSourcesPanel.tsx          # TODO: Data source config
│   │   └── ETLJobsList.tsx               # TODO: Job management UI
│   ├── ChartsSection.tsx                 # Charts tab container
│   ├── DataUploadSection.tsx             # Upload tab container
│   └── (Original components: DataUpload, FileList, NewsList, etc.)
│
├── state/
│   └── data-module.store.ts              # Zustand store for data module state
│
├── pages/
│   └── DataModule.tsx                    # Main page with tabs

shared/
└── mock-data.ts                          # Mock data with API substitution guide
```

## State Management (Zustand)

### Store Location
`client/state/data-module.store.ts`

### Store Features
```typescript
interface DataModuleStore {
  // Chart Management
  charts: Chart[]
  activeChartId: string | null
  layouts: ChartLayout[]
  currentLayout: ChartLayout | null
  
  // Chart Data
  ohlcvData: OHLCVCandle[]
  footprintData: FootprintCandle[]
  selectedTimeframe: Timeframe
  
  // UI State
  showVolumeProfile: boolean
  showDeltaProfile: boolean
  zoomLevel: "candles" | "footprint"
  indicators: ActiveIndicator[]
  
  // Actions...
}
```

### Usage Example
```typescript
import { useDataModuleStore } from '@/state/data-module.store';

const MyComponent = () => {
  const { charts, addChart, removeChart } = useDataModuleStore();
  // ...
};
```

## Components

### Chart Components

#### CandlestickChart
- **Location**: `components/data-module/charts/CandlestickChart.tsx`
- **Props**: `data`, `title`, `height`, `showVolume`
- **Status**: Ready for SciChart integration
- **TODO**: Implement SciChart rendering

#### MultiChartView
- **Location**: `components/data-module/charts/MultiChartView.tsx`
- **Features**:
  - Flexible grid layout (2x2, 3x1, 4x1, custom)
  - Add/remove charts
  - Detach charts to separate windows
  - Responsive layout
- **Uses**: Zustand store for chart management

### Indicator Components

#### IndicatorLibrary
- **Location**: `components/data-module/indicators/IndicatorLibrary.tsx`
- **Features**:
  - Categories: Volume, Momentum, Trend, Volatility, Orderflow, Custom
  - Add indicators with one click
  - Parameter templates
- **Built-in Indicators**:
  - Volume: Volume, OBV, VPT
  - Momentum: RSI, MACD, Stochastic
  - Trend: SMA, EMA, ADX
  - Volatility: Bollinger Bands, ATR
  - Orderflow: Delta, CVD

#### ActiveIndicatorsList
- **Location**: `components/data-module/indicators/ActiveIndicatorsList.tsx`
- **Features**:
  - List active indicators
  - Toggle visibility
  - Configure parameters
  - Remove indicators
  - Color coding

### ETL Components

#### ETLDashboard
- **Location**: `components/data-module/etl/ETLDashboard.tsx`
- **Features**:
  - Pipeline status overview
  - Data sources status
  - Job list with progress
  - Health monitoring
  - Auto-refresh

## Mock Data

### Location
`shared/mock-data.ts`

### Data Types
- `OHLCVCandle` - Candlestick data (Open, High, Low, Close, Volume)
- `FootprintCandle` - Orderflow data with price levels
- `VolumeProfileNode` - Volume distribution by price
- `DeltaProfileNode` - Delta accumulation over time
- `DataSource` - ETL data source configuration
- `ETLJob` - Job status and progress
- `ETLStatus` - Pipeline health status

### Functions
```typescript
// Chart Data
generateMockOHLCVData(count?, basePrice?)
generateMockFootprintData(count?)
generateMockVolumeProfile(minPrice?, maxPrice?)
generateMockDeltaProfile(count?)

// ETL Data
getMockDataSources()
getMockETLJobs()
getMockETLStatus()

// Indicators
generateMockSMAData(ohlcvData, period?)
generateMockRSIData(ohlcvData, period?)
```

### Replacing with Real API

Each function has clear comments showing the API endpoint it should call:

```typescript
/**
 * REPLACE: generateMockOHLCVData()
 * WITH: GET /api/chart/candles?symbol={symbol}&timeframe={timeframe}&start={startDate}&end={endDate}
 */
```

See `SCICHART_SETUP.md` for detailed replacement instructions.

## Tabs Overview

### Tab 1: Data Upload
- **Purpose**: Upload and process price and news data
- **Components**:
  - DataUpload selector (Prices/News)
  - FileList (Price files with processing)
  - NewsList (News files without processing)
  - File preview/details
- **Features**:
  - Drag & drop upload
  - Process button for price data
  - Timeframe transformations (30s-1w)
  - Progress tracking

### Tab 2: Charts
- **Purpose**: Analyze and visualize data
- **Sub-tabs**:
  - **Charts**: Multi-chart view with flexible grid
  - **Indicators**: Library and active indicators
- **Controls**:
  - Timeframe selector
  - Date range picker
  - Volume/Delta profile toggles
- **Features**:
  - Multiple chart layouts
  - Add/remove charts dynamically
  - Indicator management
  - Visibility toggles

### Tab 3: ETL Pipeline
- **Purpose**: Monitor data sources and jobs
- **Components**:
  - Pipeline status overview
  - Data sources list
  - Job monitoring with progress
- **Features**:
  - Real-time status updates (with mock data)
  - Job history
  - Health monitoring
  - Source connection status

## Trading Features

### Supported Timeframes
- 30 seconds
- 1 minute
- 5 minutes
- 15 minutes
- 1 hour
- 4 hours
- 1 day
- 1 week

### Data Types
- **Prices**: OHLCV candlesticks with transformations
- **News**: Feed data without transformations
- **Orderflow**: Footprint and delta data
- **Analysis**: Volume profiles and indicator overlays

### Indicators Supported
- **Trend**: SMA, EMA, ADX
- **Momentum**: RSI, MACD, Stochastic
- **Volatility**: Bollinger Bands, ATR
- **Volume**: Volume, OBV, VPT
- **Orderflow**: Delta, CVD

## UI/UX Features

- **Responsive Design**: Works on desktop (optimized for large screens)
- **Dark Theme**: Professional dark interface
- **Collapsible Sections**: Save space with collapsible indicator categories
- **Tab Navigation**: Easy switching between features
- **Resizable Panels**: Adjust layout with drag handles
- **Color Coding**: Indicators and status with visual feedback
- **Progress Tracking**: Visual indicators for upload/processing status

## Integration Points

### With Chat Assistant
The right sidebar contains the NQHUB chat assistant that persists across all tabs.

### With File Upload
New files automatically integrate with the charts and analysis.

### With Timeframe Selection
Changing timeframe updates all charts and re-generates mock data.

## Next Steps for Production

1. **Install SciChart**
   ```bash
   npm install scichart
   ```

2. **Implement Chart Rendering**
   - Update `CandlestickChart.tsx` to use SciChart
   - Implement FootprintChart
   - Add drawing tools

3. **Connect to Backend API**
   - Replace mock functions in `shared/mock-data.ts`
   - Update Zustand store actions
   - Configure API endpoints

4. **Add Real-time Updates**
   - WebSocket connection for price updates
   - Live indicator recalculation
   - ETL job streaming

5. **Performance Optimization**
   - Data windowing for large datasets
   - Caching strategy
   - Batch updates

## File Locations Quick Reference

| Component | Location |
|-----------|----------|
| Main Page | `client/pages/DataModule.tsx` |
| Zustand Store | `client/state/data-module.store.ts` |
| Mock Data | `shared/mock-data.ts` |
| Chart Components | `client/components/data-module/charts/` |
| Indicator Components | `client/components/data-module/indicators/` |
| ETL Components | `client/components/data-module/etl/` |
| Setup Guide | `SCICHART_SETUP.md` |

## Configuration

### Asset
Currently supports: **NQ Futures** (Nasdaq 100 E-mini Futures)

To change asset:
1. Update mock data generation functions
2. Update Zustand store initial state
3. Change API endpoint parameters

### Colors & Styling
- Uses Tailwind CSS with existing theme
- Color variables in theme configuration
- Indicator colors randomly assigned from palette

## Performance Considerations

- Mock data is generated on-demand
- Zustand store optimizes re-renders with selectors
- Charts use virtual scrolling for large datasets
- ETL data is paginated in the UI

## Browser Support

- Modern browsers with ES2020+ support
- React 18+ required
- TypeScript 5.9+ for development
