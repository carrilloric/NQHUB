import React, { useState } from "react";
import { Plus, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useDataModuleStore } from "@/state/data-module.store";

export interface IndicatorDefinition {
  id: string;
  name: string;
  category: "volume" | "momentum" | "trend" | "volatility" | "orderflow" | "custom";
  description: string;
  parameters: IndicatorParameter[];
}

export interface IndicatorParameter {
  name: string;
  default: number;
  min: number;
  max: number;
  step: number;
}

export const INDICATOR_LIBRARY: IndicatorDefinition[] = [
  // Volume Indicators
  {
    id: "volume",
    name: "Volume",
    category: "volume",
    description: "Trading volume",
    parameters: [],
  },
  {
    id: "obv",
    name: "On-Balance Volume",
    category: "volume",
    description: "Cumulative volume indicator",
    parameters: [],
  },
  {
    id: "vpt",
    name: "Volume Price Trend",
    category: "volume",
    description: "Relationship between volume and price change",
    parameters: [],
  },

  // Momentum Indicators
  {
    id: "rsi",
    name: "Relative Strength Index",
    category: "momentum",
    description: "Measures momentum and overbought/oversold conditions",
    parameters: [
      { name: "Period", default: 14, min: 2, max: 50, step: 1 },
    ],
  },
  {
    id: "macd",
    name: "MACD",
    category: "momentum",
    description: "Moving Average Convergence Divergence",
    parameters: [
      { name: "Fast", default: 12, min: 2, max: 50, step: 1 },
      { name: "Slow", default: 26, min: 2, max: 50, step: 1 },
      { name: "Signal", default: 9, min: 2, max: 30, step: 1 },
    ],
  },
  {
    id: "stochastic",
    name: "Stochastic Oscillator",
    category: "momentum",
    description: "Compares closing price to price range",
    parameters: [
      { name: "Period", default: 14, min: 2, max: 50, step: 1 },
      { name: "K Smooth", default: 3, min: 1, max: 20, step: 1 },
      { name: "D Smooth", default: 3, min: 1, max: 20, step: 1 },
    ],
  },

  // Trend Indicators
  {
    id: "sma",
    name: "Simple Moving Average",
    category: "trend",
    description: "Average price over a period",
    parameters: [
      { name: "Period", default: 20, min: 2, max: 200, step: 1 },
    ],
  },
  {
    id: "ema",
    name: "Exponential Moving Average",
    category: "trend",
    description: "Weighted moving average emphasizing recent data",
    parameters: [
      { name: "Period", default: 20, min: 2, max: 200, step: 1 },
    ],
  },
  {
    id: "adx",
    name: "Average Directional Index",
    category: "trend",
    description: "Measures trend strength",
    parameters: [
      { name: "Period", default: 14, min: 2, max: 50, step: 1 },
    ],
  },

  // Volatility Indicators
  {
    id: "bollinger",
    name: "Bollinger Bands",
    category: "volatility",
    description: "Volatility and overbought/oversold levels",
    parameters: [
      { name: "Period", default: 20, min: 2, max: 50, step: 1 },
      { name: "Std Dev", default: 2, min: 0.5, max: 4, step: 0.1 },
    ],
  },
  {
    id: "atr",
    name: "Average True Range",
    category: "volatility",
    description: "Measures volatility",
    parameters: [
      { name: "Period", default: 14, min: 2, max: 50, step: 1 },
    ],
  },

  // Orderflow Indicators
  {
    id: "delta",
    name: "Delta Accumulation",
    category: "orderflow",
    description: "Buy vs Sell volume accumulation",
    parameters: [],
  },
  {
    id: "cvd",
    name: "Cumulative Volume Delta",
    category: "orderflow",
    description: "Cumulative delta across candles",
    parameters: [],
  },
];

const CATEGORIES = [
  { id: "volume", label: "Volume", icon: "📊" },
  { id: "momentum", label: "Momentum", icon: "⚡" },
  { id: "trend", label: "Trend", icon: "📈" },
  { id: "volatility", label: "Volatility", icon: "📉" },
  { id: "orderflow", label: "Orderflow", icon: "🌊" },
  { id: "custom", label: "Custom", icon: "⚙️" },
];

export const IndicatorLibrary: React.FC = () => {
  const [expandedCategories, setExpandedCategories] = useState<string[]>(["momentum", "trend"]);
  const { addIndicator } = useDataModuleStore();

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    );
  };

  const handleAddIndicator = (indicator: IndicatorDefinition) => {
    const colors = ["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6"];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];

    addIndicator({
      id: `${indicator.id}-${Date.now()}`,
      name: indicator.name,
      type: indicator.id as any,
      parameters: indicator.parameters.reduce(
        (acc, param) => ({ ...acc, [param.name]: param.default }),
        {}
      ),
      visible: true,
      color: randomColor,
    });
  };

  return (
    <div className="rounded-lg border border-border bg-card flex flex-col overflow-hidden">
      <div className="p-4 border-b border-border">
        <h2 className="font-semibold">Indicator Library</h2>
        <p className="text-xs text-muted-foreground mt-1">Add indicators to your charts</p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="divide-y divide-border">
          {CATEGORIES.map((category) => {
            const indicators = INDICATOR_LIBRARY.filter((ind) => ind.category === category.id);

            return (
              <Collapsible
                key={category.id}
                open={expandedCategories.includes(category.id)}
                onOpenChange={() => toggleCategory(category.id)}
              >
                <CollapsibleTrigger className="w-full px-4 py-2 hover:bg-accent/30 transition-colors flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>{category.icon}</span>
                    <span className="font-medium text-sm">{category.label}</span>
                    <span className="text-xs text-muted-foreground">({indicators.length})</span>
                  </div>
                  <ChevronDown className="size-4 transition-transform" />
                </CollapsibleTrigger>

                <CollapsibleContent className="border-t border-border/50">
                  <div className="p-2 space-y-1">
                    {indicators.map((indicator) => (
                      <button
                        key={indicator.id}
                        onClick={() => handleAddIndicator(indicator)}
                        className="w-full text-left px-3 py-2 rounded-md hover:bg-accent/50 transition-colors flex items-center justify-between group"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{indicator.name}</p>
                          <p className="text-xs text-muted-foreground line-clamp-1">
                            {indicator.description}
                          </p>
                        </div>
                        <Plus className="size-3 text-muted-foreground group-hover:text-foreground opacity-0 group-hover:opacity-100 transition-all flex-shrink-0 ml-2" />
                      </button>
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            );
          })}
        </div>
      </div>
    </div>
  );
};
