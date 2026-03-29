import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

// Mock strategies database
const mockStrategies = [
  {
    id: 'strategy-1',
    name: 'FVG Retest Strategy',
    type: 'RuleBasedStrategy',
    code: `from nqhub.strategies.base import RuleBasedStrategy
import pandas as pd

class FVGRetestStrategy(RuleBasedStrategy):

    def required_features(self) -> list[str]:
        return ['active_fvgs', 'bias', 'session']

    def generate_signals(self, market_state) -> pd.Series:
        signals = pd.Series(0, index=market_state.index)
        # FVG retest logic here
        return signals

    def position_size(self) -> int:
        return 1
`,
  },
  {
    id: 'strategy-2',
    name: 'Order Block Strategy',
    type: 'RuleBasedStrategy',
    code: `from nqhub.strategies.base import RuleBasedStrategy
import pandas as pd

class OrderBlockStrategy(RuleBasedStrategy):

    def required_features(self) -> list[str]:
        return ['active_obs', 'displacement', 'volume']

    def generate_signals(self, market_state) -> pd.Series:
        signals = pd.Series(0, index=market_state.index)
        # Order block logic here
        return signals

    def position_size(self) -> int:
        return 2
`,
  },
  {
    id: 'strategy-3',
    name: 'ICT Kill Zones Strategy',
    type: 'RuleBasedStrategy',
    code: `from nqhub.strategies.base import RuleBasedStrategy
import pandas as pd

class KillZonesStrategy(RuleBasedStrategy):

    def required_features(self) -> list[str]:
        return ['session', 'bias', 'liquidity_pools']

    def generate_signals(self, market_state) -> pd.Series:
        signals = pd.Series(0, index=market_state.index)
        # Kill zones logic here
        return signals

    def position_size(self) -> int:
        return 1
`,
  },
];

export const strategiesHandlers = [
  // Validate strategy code
  http.post(`${API_BASE}/strategies/validate`, async ({ request }) => {
    const body = await request.json() as { code: string };
    const code = body.code || '';

    // Simple validation: check if code contains required class definition
    const hasClass = code.includes('class ') && code.includes('Strategy');
    const hasMethods =
      code.includes('required_features') &&
      code.includes('generate_signals') &&
      code.includes('position_size');

    if (hasClass && hasMethods) {
      // Extract strategy name from class definition
      const classMatch = code.match(/class\s+(\w+)\s*\(/);
      const strategyName = classMatch ? classMatch[1] : 'MiEstrategia';

      // Extract strategy type
      const typeMatch = code.match(/\(\s*(\w+)\s*\)/);
      const strategyType = typeMatch ? typeMatch[1] : 'RuleBasedStrategy';

      // Mock feature extraction
      const featuresMatch = code.match(/return\s+\[(.*?)\]/);
      let features = ['delta', 'poc', 'cvd'];
      if (featuresMatch) {
        features = featuresMatch[1]
          .split(',')
          .map((f) => f.trim().replace(/['"]/g, ''))
          .filter((f) => f.length > 0);
      }

      return HttpResponse.json({
        valid: true,
        strategy_name: strategyName,
        strategy_type: strategyType,
        required_features: features,
      });
    }

    return HttpResponse.json({
      valid: false,
      errors: [
        'Missing required class definition',
        'Strategy must inherit from RuleBasedStrategy, MLStrategy, or RLStrategy',
        'Required methods: required_features, generate_signals, position_size',
      ],
    });
  }),

  // Register strategy
  http.post(`${API_BASE}/strategies/register`, async ({ request }) => {
    const body = await request.json() as { code: string; name: string; type: string; description: string };

    // Simulate successful registration
    const newStrategy = {
      id: `strategy-${Date.now()}`,
      name: body.name,
      type: body.type,
      code: body.code,
    };

    mockStrategies.push(newStrategy);

    return HttpResponse.json({
      strategy_id: newStrategy.id,
      status: 'draft',
      message: 'Strategy registered successfully',
    });
  }),

  // Get all strategies
  http.get(`${API_BASE}/strategies`, () => {
    return HttpResponse.json({
      strategies: mockStrategies,
      count: mockStrategies.length,
    });
  }),

  // Legacy endpoint for backwards compatibility
  http.post(`${API_BASE}/strategies/save`, () => HttpResponse.json({ id: 'strategy-1', status: 'saved' })),
];