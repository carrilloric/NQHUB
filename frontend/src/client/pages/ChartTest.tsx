import React, { useState, useEffect } from 'react';
import { ProfessionalChart } from '@/components/data-module/charts/ProfessionalChart';
import { DatePicker } from '@/components/ui/date-picker';
import { format } from 'date-fns';
import { fromZonedTime, toZonedTime } from 'date-fns-tz';

export default function ChartTest() {
  // State for symbol selection and date/time controls
  const [symbol, setSymbol] = useState('NQZ5'); // Default to NQZ5 (most recent data)
  const [selectedDate, setSelectedDate] = useState<Date>(new Date('2025-11-20T09:30:00'));
  const [timeInput, setTimeInput] = useState('09:30');
  const [availableSymbols, setAvailableSymbols] = useState<string[]>(['NQZ5', 'NQH6', 'NQM4']);

  // Calculated state
  const [startDate, setStartDate] = useState(new Date('2025-11-20T09:30:00'));
  const [endDate, setEndDate] = useState(new Date('2025-11-20T21:30:00')); // +12 hours

  // Update start/end dates when date or time changes
  // IMPORTANT: User selects time in ET (Eastern Time), we convert to UTC for API
  useEffect(() => {
    if (selectedDate && timeInput) {
      const [hours, minutes] = timeInput.split(':').map(Number);

      // Create date in ET timezone
      const dateInET = new Date(selectedDate);
      dateInET.setHours(hours, minutes, 0, 0);

      // Convert ET to UTC for API calls
      // America/New_York handles EST/EDT automatically
      const startUTC = fromZonedTime(dateInET, 'America/New_York');
      const endUTC = new Date(startUTC.getTime() + 12 * 60 * 60 * 1000); // +12 hours in UTC

      setStartDate(startUTC);
      setEndDate(endUTC);
    }
  }, [selectedDate, timeInput]);

  // Fetch available symbols on mount
  useEffect(() => {
    fetch('/api/v1/candles/symbols/available')
      .then(res => res.json())
      .then(data => {
        const symbols = data.map((s: any) => s.symbol);
        setAvailableSymbols(symbols);
      })
      .catch(err => console.error('Failed to fetch symbols:', err));
  }, []);

  const handleZoomIn = () => {
    const chartContainer = document.querySelector('.tv-lightweight-charts') as HTMLElement;
    if (chartContainer) {
      // Simulate zoom in with wheel event
      const event = new WheelEvent('wheel', {
        deltaY: -500,
        clientX: chartContainer.offsetWidth / 2,
        clientY: chartContainer.offsetHeight / 2,
        bubbles: true,
      });
      chartContainer.dispatchEvent(event);
    }
  };

  const handleZoomOut = () => {
    const chartContainer = document.querySelector('.tv-lightweight-charts') as HTMLElement;
    if (chartContainer) {
      // Simulate zoom out with wheel event
      const event = new WheelEvent('wheel', {
        deltaY: 500,
        clientX: chartContainer.offsetWidth / 2,
        clientY: chartContainer.offsetHeight / 2,
        bubbles: true,
      });
      chartContainer.dispatchEvent(event);
    }
  };

  const handleResetZoom = () => {
    const chartContainer = document.querySelector('.tv-lightweight-charts') as HTMLElement;
    if (chartContainer) {
      // Simulate double click to fit content
      const event = new MouseEvent('dblclick', {
        clientX: chartContainer.offsetWidth / 2,
        clientY: chartContainer.offsetHeight / 2,
        bubbles: true,
      });
      chartContainer.dispatchEvent(event);
    }
  };

  // Calculate candle count (assuming 5min candles)
  const candleCount = Math.round((endDate.getTime() - startDate.getTime()) / (5 * 60 * 1000));

  return (
    <div className="min-h-screen bg-[#070c16] p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-6">
          Professional Chart Test - Database Connected (Eastern Time)
        </h1>

        {/* Data Selection Controls */}
        <div className="mb-6 p-6 bg-[#111c2d] rounded-lg border border-border/40">
          <h2 className="text-lg font-semibold text-white mb-4">Data Selection</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Symbol Selector */}
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Symbol
              </label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full px-3 py-2 bg-[#0d1726] border border-border/40 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {availableSymbols.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Date Picker */}
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Date
              </label>
              <DatePicker
                date={selectedDate}
                onDateChange={(date) => date && setSelectedDate(date)}
                placeholder="Select date"
              />
            </div>

            {/* Time Input */}
            <div>
              <label className="block text-sm font-medium text-muted-foreground mb-2">
                Start Time (ET)
              </label>
              <input
                type="time"
                value={timeInput}
                onChange={(e) => setTimeInput(e.target.value)}
                className="w-full px-3 py-2 bg-[#0d1726] border border-border/40 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            {/* Info Display */}
            <div className="flex items-end">
              <div className="w-full px-3 py-2 bg-primary/10 border border-primary/40 rounded-lg">
                <div className="text-xs text-muted-foreground">Period</div>
                <div className="text-sm font-semibold text-primary">12 hours</div>
                <div className="text-xs text-muted-foreground">~{candleCount} candles</div>
              </div>
            </div>
          </div>

          {/* Date Range Display */}
          <div className="mt-4 p-3 bg-[#0d1726]/50 rounded border border-border/20">
            <div className="text-sm text-muted-foreground">
              <span className="font-semibold text-white">Period (ET):</span>{' '}
              {format(toZonedTime(startDate, 'America/New_York'), 'PPP HH:mm')} → {format(toZonedTime(endDate, 'America/New_York'), 'PPP HH:mm')} ET
            </div>
            <div className="text-xs text-muted-foreground/60 mt-1">
              ⏰ Times shown in Eastern Time (Market hours: 09:30-16:00 ET)
            </div>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex gap-3 mb-4">
          <button
            onClick={handleZoomIn}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-colors"
          >
            Zoom In (+)
          </button>
          <button
            onClick={handleZoomOut}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-colors"
          >
            Zoom Out (-)
          </button>
          <button
            onClick={handleResetZoom}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
          >
            Reset Zoom
          </button>
        </div>

        {/* Chart */}
        <div className="h-[800px]">
          <ProfessionalChart
            symbol={symbol}
            timeframe="5m"
            startDate={startDate}
            endDate={endDate}
            height={700}
            showVolumeProfile={true}
            onDetach={() => console.log('Detach clicked')}
          />
        </div>

        {/* Info Panel */}
        <div className="mt-6 p-4 bg-[#111c2d] rounded-lg text-white border border-border/40">
          <h2 className="font-bold mb-2">Current Configuration:</h2>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><span className="text-muted-foreground">Symbol:</span> <span className="font-mono">{symbol}</span></div>
            <div><span className="text-muted-foreground">Timeframe:</span> <span className="font-mono">5m</span></div>
            <div><span className="text-muted-foreground">Start (ET):</span> <span className="font-mono">{format(toZonedTime(startDate, 'America/New_York'), 'PPP HH:mm')}</span></div>
            <div><span className="text-muted-foreground">End (ET):</span> <span className="font-mono">{format(toZonedTime(endDate, 'America/New_York'), 'PPP HH:mm')}</span></div>
            <div><span className="text-muted-foreground">Expected Candles:</span> <span className="font-mono">~{candleCount}</span></div>
            <div><span className="text-muted-foreground">Data Source:</span> <span className="font-mono text-green-400">PostgreSQL</span></div>
            <div className="col-span-2"><span className="text-muted-foreground">Timezone:</span> <span className="font-mono text-yellow-400">Eastern Time (EST/EDT)</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
