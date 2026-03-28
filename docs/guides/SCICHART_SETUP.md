# SciChart Setup & Mock Data Guide

## Installation

SciChart is a professional charting library that requires installation:

```bash
npm install scichart
```

## Architecture Overview

The Data Module uses the following architecture:

### State Management (Zustand)
- **Store Location**: `client/state/data-module.store.ts`
- **Features**:
  - Chart management (add, remove, update, organize)
  - Chart data (OHLCV, Footprint)
  - Timeframe selection
  - Indicator management
  - Layout management

### Mock Data System
- **Location**: `shared/mock-data.ts`
- **Purpose**: Development and testing without backend
- **All functions are clearly marked for API substitution**

## Replacing Mock Data with Real API Calls

### Step 1: Install SciChart
```bash
npm install scichart
```

### Step 2: Configure SciChart License (if needed)
```typescript
// At app initialization
import { SciChartSurface } from 'scichart';

SciChartSurface.setRuntimeLicenseKey('YOUR_LICENSE_KEY');
```

### Step 3: Replace Mock Functions with API Calls

#### Example: Replacing `generateMockOHLCVData()`

**Current Mock (in shared/mock-data.ts):**
```typescript
export function generateMockOHLCVData(count: number = 100, basePrice: number = 18500): OHLCVCandle[] {
  // ... mock implementation
}
```

**Replace with API Call:**
```typescript
export async function getOHLCVData(
  symbol: string = "NQ",
  timeframe: string = "1h",
  startDate: Date,
  endDate: Date
): Promise<OHLCVCandle[]> {
  const response = await fetch(
    `/api/chart/candles?symbol=${symbol}&timeframe=${timeframe}&start=${startDate.toISOString()}&end=${endDate.toISOString()}`
  );
  if (!response.ok) throw new Error('Failed to fetch OHLCV data');
  return response.json();
}
```

### Step 4: Update Store to Use New API

**In client/state/data-module.store.ts:**

Before:
```typescript
setTimeframe: (timeframe) =>
  set((state) => ({
    selectedTimeframe: timeframe,
    ohlcvData: generateMockOHLCVData(100),
  })),
```

After:
```typescript
setTimeframe: (timeframe) =>
  set(async (state) => {
    const newData = await getOHLCVData("NQ", timeframe, new Date(), new Date());
    return {
      selectedTimeframe: timeframe,
      ohlcvData: newData,
    };
  }),
```

## API Endpoints Reference

Based on the mock data structure, the backend should implement:

### Chart Data Endpoints
```
GET /api/chart/candles?symbol=NQ&timeframe=1h&start=ISO_DATE&end=ISO_DATE
→ Returns: OHLCVCandle[]

GET /api/chart/footprint?symbol=NQ&timeframe=1h&start=ISO_DATE&end=ISO_DATE
→ Returns: FootprintCandle[]

GET /api/chart/volume-profile?symbol=NQ&timeframe=1h&start=ISO_DATE&end=ISO_DATE
→ Returns: VolumeProfileNode[]

GET /api/chart/delta-profile?symbol=NQ&timeframe=1h&start=ISO_DATE&end=ISO_DATE
→ Returns: DeltaProfileNode[]
```

### Indicator Endpoints
```
GET /api/indicators/sma?symbol=NQ&period=20&timeframe=1h
→ Returns: IndicatorValue[]

GET /api/indicators/rsi?symbol=NQ&period=14&timeframe=1h
→ Returns: IndicatorValue[]
```

### ETL Endpoints
```
GET /api/etl/status
→ Returns: ETLStatus

GET /api/etl/sources
→ Returns: DataSource[]

GET /api/etl/jobs
→ Returns: ETLJob[]

GET /api/etl/jobs/:jobId
→ Returns: ETLJob

POST /api/etl/jobs/:jobId/retry
→ Returns: ETLJob
```

## Component Structure

### Charts
- **CandlestickChart** (`components/data-module/charts/CandlestickChart.tsx`)
  - Displays OHLCV data
  - TODO: Implement with SciChart
  
- **MultiChartView** (`components/data-module/charts/MultiChartView.tsx`)
  - Container for multiple charts
  - Flexible grid (2x2, 3x1, 4x1, custom)
  - Uses Zustand store for chart management

### Indicators
- **IndicatorLibrary** (`components/data-module/indicators/IndicatorLibrary.tsx`)
  - Browse available indicators by category
  - Add indicators to active list
  
- **ActiveIndicatorsList** (`components/data-module/indicators/ActiveIndicatorsList.tsx`)
  - List of active indicators
  - Toggle visibility
  - Configure parameters
  - Remove indicators

### ETL
- **ETLDashboard** (`components/data-module/etl/ETLDashboard.tsx`)
  - Pipeline status
  - Data sources status
  - Job management

## Development Workflow

1. **Use Mocks During Development**
   - All mock data is in `shared/mock-data.ts`
   - Zustand store provides UI state management
   - Components work with mock data

2. **Test UI Without Backend**
   - Run the app with npm run dev
   - Mock data automatically loads
   - Test all features

3. **When Backend is Ready**
   - Replace mock functions with API calls
   - Update store actions to use async API calls
   - No UI changes needed (contracts remain the same)

4. **Deploy**
   - Install SciChart license key
   - Configure API endpoints
   - Deploy to production

## TypeScript Interfaces

All data structures are defined in `shared/mock-data.ts`:

- `OHLCVCandle` - Single candlestick data
- `FootprintCandle` - Footprint/orderflow data
- `FootprintLevel` - Price level in footprint
- `VolumeProfileNode` - Volume at price level
- `DeltaProfileNode` - Delta over time
- `DataSource` - ETL data source
- `ETLJob` - ETL job status
- `ETLStatus` - Overall ETL status
- `IndicatorValue` - Indicator data point
- `IndicatorDefinition` - Indicator metadata (in IndicatorLibrary.tsx)
- `IndicatorParameter` - Indicator parameter definition

## Troubleshooting

### SciChart License Key
If you see license errors, ensure the key is set before creating any surfaces:
```typescript
import { SciChartSurface } from 'scichart';
SciChartSurface.setRuntimeLicenseKey('YOUR_KEY');
```

### Performance with Large Datasets
- Use candle aggregation for large timeframes
- Implement data windowing for visible area
- Cache processed data in Zustand store

### Real-time Updates
When implementing real-time updates:
1. Use WebSocket for price updates
2. Update Zustand store with new data
3. SciChart will automatically re-render

## Next Steps

1. ✅ SciChart library installed
2. ⏳ Implement CandlestickChart.tsx with SciChart
3. ⏳ Connect to real API endpoints
4. ⏳ Add real-time WebSocket support
5. ⏳ Implement drawing tools and annotations
6. ⏳ Add DOM exports and charts to file
