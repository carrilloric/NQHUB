# Server Time Implementation

## Overview

NQHUB now has a centralized server time system that provides a single source of truth for date/time across the entire application. The server time is maintained in Eastern Time (ET) with automatic Daylight Saving Time (DST) handling.

## Architecture

### Backend (FastAPI)

#### Endpoints

**`GET /api/v1/system/time`**
- Returns current server time in multiple formats
- No authentication required (public endpoint)
- Response includes:
  - `utc`: UTC time (timezone-aware)
  - `et`: Eastern Time (timezone-aware)
  - `et_naive`: ET string for display (YYYY-MM-DD HH:MM:SS)
  - `timezone`: Current timezone setting (America/New_York)
  - `offset_hours`: Current offset from UTC (-5 or -4 with DST)
  - `is_dst`: Whether DST is currently in effect

**`GET /api/v1/system/config`**
- Returns system configuration including timezone settings
- Provides list of available trading timezones for future configuration

**`GET /api/v1/system/heartbeat`**
- Lightweight endpoint for connection checks
- Returns server status and current ET time

### Frontend (React)

#### ServerTimeProvider Context

Located at: `frontend/src/client/state/server-time.tsx`

**Features:**
- Automatic synchronization every 60 seconds
- Heartbeat checks every 5 seconds for connection status
- Client-server time offset calculation for accurate local updates
- Re-sync when browser tab becomes active
- Real-time clock updates every second

**Available through `useServerTime()` hook:**
```typescript
const {
  serverTime,         // Current server time data
  getCurrentTime,     // Get calculated current time
  getFormattedET,     // Get "YYYY-MM-DD HH:MM:SS ET (UTC)" format
  getFormattedUTC,    // Get UTC formatted time
  syncTime,           // Manual sync trigger
  isConnected,        // Connection status
  lastSyncTime,       // Last successful sync
  syncError          // Error message if any
} = useServerTime();
```

#### ServerTimeClock Component

Located at: `frontend/src/client/components/common/ServerTimeClock.tsx`

**Props:**
- `format`: Display format ('full' | 'et' | 'compact')
- `showIcon`: Show clock icon (default: true)
- `className`: Custom styling

**Display Formats:**
- `full`: "2024-11-29 14:30:45 ET (19:30:45 UTC)"
- `et`: "2024-11-29 14:30:45 ET"
- `compact`: "14:30:45 ET"

**Visual Indicators:**
- Green: Connected and synced
- Yellow: Sync error (with warning icon)
- Red: Disconnected (with offline icon)

## Integration

The server time is integrated into the application at multiple levels:

1. **App Level**: `ServerTimeProvider` wraps the entire application in `App.tsx`
2. **TopNavbar**: Displays server time next to market ticker
3. **Available Globally**: Any component can use `useServerTime()` hook

## Usage Examples

### Getting Current Server Time

```typescript
import { useServerTime } from '@/state/server-time';

function MyComponent() {
  const { getCurrentTime, getFormattedET } = useServerTime();

  const handleSubmit = () => {
    const currentTime = getCurrentTime();
    console.log('Current ET:', currentTime?.etNaive);
    console.log('Full format:', getFormattedET());
  };

  return <div>...</div>;
}
```

### Displaying Server Time

```tsx
import { ServerTimeClock } from '@/components/common/ServerTimeClock';

function Dashboard() {
  return (
    <div>
      <ServerTimeClock format="compact" />
    </div>
  );
}
```

### Converting Dates to ET Format

```typescript
import { formatToET } from '@/state/server-time';

const etString = formatToET(new Date()); // "2024-11-29 14:30:45 ET"
```

## Configuration

### Sync Intervals

- **Full Sync**: Every 60 seconds
- **Heartbeat**: Every 5 seconds
- **Clock Update**: Every 1 second

These can be modified in `server-time.tsx`:
```typescript
const SYNC_INTERVAL = 60000;      // 60 seconds
const HEARTBEAT_INTERVAL = 5000;  // 5 seconds
```

### Timezone Configuration

The default timezone is `America/New_York` (Eastern Time). Future implementation will allow configuration through settings.

Available trading timezones (for future use):
- America/New_York (ET - US Markets)
- America/Chicago (CT - CME)
- America/Los_Angeles (PT)
- Europe/London (GMT/BST - LSE)
- Europe/Frankfurt (CET - Eurex)
- Asia/Tokyo (JST - TSE)
- Asia/Hong_Kong (HKT - HKEX)
- Asia/Singapore (SGT - SGX)
- Australia/Sydney (AEDT - ASX)

## Benefits

1. **Single Source of Truth**: All time-sensitive operations reference the same server time
2. **Timezone Consistency**: Eliminates client timezone issues
3. **DST Handling**: Automatic Daylight Saving Time adjustments
4. **Connection Monitoring**: Visual indicators for sync status
5. **Performance**: Efficient polling with smart re-sync on tab activation
6. **Accuracy**: Client-server offset calculation for precise time display

## Future Enhancements

1. **User Preferences**: Allow users to select preferred display timezone
2. **Market Hours**: Integrate with market session times
3. **Time Zone Converter**: Tool for converting between trading timezones
4. **Audit Logging**: Include server time in all audit entries
5. **Historical Playback**: Use server time for backtesting scenarios

## Troubleshooting

### Clock Not Updating
- Check browser console for sync errors
- Verify backend is running on port 8002
- Check network connectivity

### Time Offset Issues
- Server time is always in ET (Eastern Time)
- Client displays are calculated from UTC with offset
- Verify system time on server is correct

### Connection Issues
- Red indicator means disconnected from server
- Yellow indicator means sync errors (check console)
- Green indicator means connected and synced

## Related Files

- Backend endpoint: `backend/app/api/v1/endpoints/system.py`
- Frontend context: `frontend/src/client/state/server-time.tsx`
- Clock component: `frontend/src/client/components/common/ServerTimeClock.tsx`
- Integration: `frontend/src/client/components/layout/TopNavbar.tsx`