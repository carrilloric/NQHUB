import { create } from "zustand";
import { OHLCVCandle, FootprintCandle, generateMockOHLCVData, generateMockFootprintData } from "@shared/mock-data";

// ==================== TYPES ====================
export type ChartType = "candlestick" | "footprint";
export type Timeframe = "30s" | "1m" | "5m" | "15m" | "1h" | "4h" | "1d" | "1w";

export interface Chart {
  id: string;
  title: string;
  type: ChartType;
  timeframe: Timeframe;
  data: OHLCVCandle[] | FootprintCandle[];
  isDetached: boolean;
}

export interface ChartLayout {
  id: string;
  name: string;
  gridConfig: "2x2" | "3x1" | "4x1" | "custom";
  charts: Chart[];
  createdAt: Date;
}

export interface ActiveIndicator {
  id: string;
  name: string;
  type: "sma" | "rsi" | "macd" | "bollinger" | "custom";
  parameters: Record<string, number>;
  visible: boolean;
  color: string;
}

// ==================== STORE ====================
interface DataModuleStore {
  // Chart Management
  charts: Chart[];
  activeChartId: string | null;
  layouts: ChartLayout[];
  currentLayout: ChartLayout | null;

  // Chart Data
  ohlcvData: OHLCVCandle[];
  footprintData: FootprintCandle[];
  selectedTimeframe: Timeframe;

  // UI State
  showVolumeProfile: boolean;
  showDeltaProfile: boolean;
  zoomLevel: "candles" | "footprint";
  indicators: ActiveIndicator[];

  // Actions
  addChart: (chart: Chart) => void;
  removeChart: (chartId: string) => void;
  updateChart: (chartId: string, updates: Partial<Chart>) => void;
  setActiveChart: (chartId: string | null) => void;

  setOHLCVData: (data: OHLCVCandle[]) => void;
  setFootprintData: (data: FootprintCandle[]) => void;
  setTimeframe: (timeframe: Timeframe) => void;

  setShowVolumeProfile: (show: boolean) => void;
  setShowDeltaProfile: (show: boolean) => void;
  setZoomLevel: (level: "candles" | "footprint") => void;

  addIndicator: (indicator: ActiveIndicator) => void;
  removeIndicator: (indicatorId: string) => void;
  updateIndicator: (indicatorId: string, updates: Partial<ActiveIndicator>) => void;
  toggleIndicatorVisibility: (indicatorId: string) => void;

  createLayout: (layout: ChartLayout) => void;
  setCurrentLayout: (layout: ChartLayout) => void;
  loadLayout: (layoutId: string) => void;
  deleteLayout: (layoutId: string) => void;
}

export const useDataModuleStore = create<DataModuleStore>((set, get) => {
  // Initialize with mock data
  const initialOHLCVData = generateMockOHLCVData(100);
  const initialFootprintData = generateMockFootprintData(50);

  const defaultLayout: ChartLayout = {
    id: "default",
    name: "Default Layout",
    gridConfig: "2x2",
    charts: [
      {
        id: "chart-1",
        title: "NQ 1H Chart",
        type: "candlestick",
        timeframe: "1h",
        data: initialOHLCVData,
        isDetached: false,
      },
      {
        id: "chart-2",
        title: "NQ 15M Chart",
        type: "candlestick",
        timeframe: "15m",
        data: generateMockOHLCVData(100),
        isDetached: false,
      },
    ],
    createdAt: new Date(),
  };

  return {
    // Initial state
    charts: defaultLayout.charts,
    activeChartId: "chart-1",
    layouts: [defaultLayout],
    currentLayout: defaultLayout,

    ohlcvData: initialOHLCVData,
    footprintData: initialFootprintData,
    selectedTimeframe: "1h",

    showVolumeProfile: false,
    showDeltaProfile: false,
    zoomLevel: "candles",
    indicators: [],

    // Chart Management Actions
    addChart: (chart) =>
      set((state) => ({
        charts: [...state.charts, chart],
      })),

    removeChart: (chartId) =>
      set((state) => ({
        charts: state.charts.filter((c) => c.id !== chartId),
        activeChartId: state.activeChartId === chartId ? null : state.activeChartId,
      })),

    updateChart: (chartId, updates) =>
      set((state) => ({
        charts: state.charts.map((c) => (c.id === chartId ? { ...c, ...updates } : c)),
      })),

    setActiveChart: (chartId) =>
      set(() => ({
        activeChartId: chartId,
      })),

    // Chart Data Actions
    setOHLCVData: (data) =>
      set(() => ({
        ohlcvData: data,
      })),

    setFootprintData: (data) =>
      set(() => ({
        footprintData: data,
      })),

    setTimeframe: (timeframe) =>
      set((state) => ({
        selectedTimeframe: timeframe,
        ohlcvData: generateMockOHLCVData(100),
      })),

    // UI State Actions
    setShowVolumeProfile: (show) =>
      set(() => ({
        showVolumeProfile: show,
      })),

    setShowDeltaProfile: (show) =>
      set(() => ({
        showDeltaProfile: show,
      })),

    setZoomLevel: (level) =>
      set(() => ({
        zoomLevel: level,
      })),

    // Indicator Actions
    addIndicator: (indicator) =>
      set((state) => ({
        indicators: [...state.indicators, indicator],
      })),

    removeIndicator: (indicatorId) =>
      set((state) => ({
        indicators: state.indicators.filter((i) => i.id !== indicatorId),
      })),

    updateIndicator: (indicatorId, updates) =>
      set((state) => ({
        indicators: state.indicators.map((i) => (i.id === indicatorId ? { ...i, ...updates } : i)),
      })),

    toggleIndicatorVisibility: (indicatorId) =>
      set((state) => ({
        indicators: state.indicators.map((i) =>
          i.id === indicatorId ? { ...i, visible: !i.visible } : i
        ),
      })),

    // Layout Actions
    createLayout: (layout) =>
      set((state) => ({
        layouts: [...state.layouts, layout],
        currentLayout: layout,
        charts: layout.charts,
      })),

    setCurrentLayout: (layout) =>
      set(() => ({
        currentLayout: layout,
        charts: layout.charts,
      })),

    loadLayout: (layoutId) =>
      set((state) => {
        const layout = state.layouts.find((l) => l.id === layoutId);
        if (!layout) return state;
        return {
          currentLayout: layout,
          charts: layout.charts,
        };
      }),

    deleteLayout: (layoutId) =>
      set((state) => ({
        layouts: state.layouts.filter((l) => l.id !== layoutId),
        currentLayout: state.currentLayout?.id === layoutId ? null : state.currentLayout,
      })),
  };
});
