import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { CheckCircle2, XCircle, Play } from 'lucide-react';

const INITIAL_TEMPLATE = `from nqhub.strategies.base import RuleBasedStrategy
import pandas as pd

class MiEstrategia(RuleBasedStrategy):

    def required_features(self) -> list[str]:
        return ['delta', 'poc', 'cvd']

    def generate_signals(self, market_state) -> pd.Series:
        # Tu lógica aquí
        signals = pd.Series(0, index=market_state.index)
        return signals

    def position_size(self) -> int:
        return 1
`;

interface ValidationResult {
  valid: boolean;
  strategy_name?: string;
  strategy_type?: string;
  required_features?: string[];
  errors?: string[];
}

interface Strategy {
  id: string;
  name: string;
  type: string;
  code: string;
}

export default function AlphaLab() {
  const [code, setCode] = useState(INITIAL_TEMPLATE);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>('');
  const [strategyName, setStrategyName] = useState('');
  const [strategyDescription, setStrategyDescription] = useState('');
  const { toast } = useToast();
  const navigate = useNavigate();

  // Load strategies on mount
  useState(() => {
    fetch('/api/v1/strategies')
      .then((res) => res.json())
      .then((data) => setStrategies(data.strategies || []))
      .catch((err) => console.error('Failed to load strategies:', err));
  });

  const handleValidate = async () => {
    setIsValidating(true);
    try {
      const response = await fetch('/api/v1/strategies/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      const result = await response.json();
      setValidationResult(result);
    } catch (error) {
      setValidationResult({
        valid: false,
        errors: ['Failed to validate strategy. Please try again.'],
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleRegisterClick = () => {
    if (validationResult?.valid) {
      setStrategyName(validationResult.strategy_name || '');
      setShowRegisterModal(true);
    }
  };

  const handleRegister = async () => {
    if (!strategyName.trim()) {
      toast({
        title: 'Error',
        description: 'Strategy name is required',
        variant: 'destructive',
      });
      return;
    }

    setIsRegistering(true);
    try {
      const response = await fetch('/api/v1/strategies/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code,
          name: strategyName,
          type: validationResult?.strategy_type || 'rule_based',
          description: strategyDescription,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        toast({
          title: 'Success',
          description: 'Estrategia registrada — ya puedes correr un backtest',
        });
        setShowRegisterModal(false);
        setStrategyName('');
        setStrategyDescription('');
        // Reload strategies list
        const strategiesResponse = await fetch('/api/v1/strategies');
        const strategiesData = await strategiesResponse.json();
        setStrategies(strategiesData.strategies || []);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to register strategy',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to register strategy',
        variant: 'destructive',
      });
    } finally {
      setIsRegistering(false);
    }
  };

  const handleLoadStrategy = () => {
    const strategy = strategies.find((s) => s.id === selectedStrategyId);
    if (strategy) {
      setCode(strategy.code);
      setValidationResult(null); // Clear validation when loading new code
    }
  };

  const handleRunBacktest = () => {
    if (validationResult?.valid) {
      navigate('/backtesting/rule-based', {
        state: {
          strategy: {
            name: validationResult.strategy_name,
            type: validationResult.strategy_type,
            code,
          },
        },
      });
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <h1 className="text-2xl font-bold text-white">ALPHA LAB</h1>
        <div className="flex gap-2">
          <Button
            onClick={handleValidate}
            disabled={isValidating}
            variant="outline"
            className="bg-gray-800 hover:bg-gray-700 text-white border-gray-600"
          >
            {isValidating ? 'Validating...' : 'Validate'}
          </Button>
          <Button
            onClick={handleRegisterClick}
            disabled={!validationResult?.valid || isRegistering}
            className="bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-700 disabled:text-gray-500"
          >
            {isRegistering ? 'Registering...' : 'Register'}
          </Button>
        </div>
      </div>

      {/* Main Content - 2 columns */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel - Editor */}
        <div className="flex-1 border-r border-gray-700">
          <Editor
            height="100%"
            defaultLanguage="python"
            theme="vs-dark"
            value={code}
            onChange={(value) => setCode(value || '')}
            options={{
              fontSize: 14,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              automaticLayout: true,
            }}
          />
        </div>

        {/* Right Panel - Output */}
        <div className="w-96 bg-gray-800 p-4 flex flex-col">
          <h2 className="text-lg font-semibold text-white mb-4">Output Panel</h2>

          {validationResult && (
            <div className="flex-1 overflow-y-auto">
              {validationResult.valid ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-green-400">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-semibold">Valid strategy</span>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-gray-400">Strategy:</span>{' '}
                      <span className="text-white">{validationResult.strategy_name}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Type:</span>{' '}
                      <span className="text-white">{validationResult.strategy_type}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Features:</span>{' '}
                      <span className="text-white">
                        {JSON.stringify(validationResult.required_features)}
                      </span>
                    </div>
                  </div>

                  <div className="border-t border-gray-700 pt-4 mt-4">
                    <Button
                      onClick={handleRunBacktest}
                      className="w-full bg-green-600 hover:bg-green-700"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Run Quick Backtest
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-red-400">
                    <XCircle className="w-5 h-5" />
                    <span className="font-semibold">Validation failed</span>
                  </div>

                  <div className="space-y-2">
                    {validationResult.errors?.map((error, index) => (
                      <div
                        key={index}
                        className="text-sm text-red-300 bg-red-900/20 p-2 rounded border border-red-800"
                      >
                        {error}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!validationResult && (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <p className="text-sm text-center">
                Click "Validate" to check your strategy
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Panel - Strategy Selector */}
      <div className="border-t border-gray-700 p-4 bg-gray-800">
        <div className="flex items-center gap-4">
          <Label htmlFor="strategy-select" className="text-white whitespace-nowrap">
            Strategy selector:
          </Label>
          <Select value={selectedStrategyId} onValueChange={setSelectedStrategyId}>
            <SelectTrigger id="strategy-select" className="w-64 bg-gray-900 border-gray-600 text-white">
              <SelectValue placeholder="Select existing" />
            </SelectTrigger>
            <SelectContent className="bg-gray-900 border-gray-700">
              {strategies.map((strategy) => (
                <SelectItem key={strategy.id} value={strategy.id} className="text-white">
                  {strategy.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleLoadStrategy}
            disabled={!selectedStrategyId}
            variant="outline"
            className="bg-gray-900 hover:bg-gray-700 text-white border-gray-600"
          >
            Load
          </Button>
        </div>
      </div>

      {/* Register Modal */}
      <Dialog open={showRegisterModal} onOpenChange={setShowRegisterModal}>
        <DialogContent className="bg-gray-800 border-gray-700 text-white">
          <DialogHeader>
            <DialogTitle>Register Strategy</DialogTitle>
            <DialogDescription className="text-gray-400">
              Provide a name and description for your strategy
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Strategy Name</Label>
              <Input
                id="name"
                value={strategyName}
                onChange={(e) => setStrategyName(e.target.value)}
                placeholder="My ICT Strategy"
                className="bg-gray-900 border-gray-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={strategyDescription}
                onChange={(e) => setStrategyDescription(e.target.value)}
                placeholder="Strategy description..."
                rows={4}
                className="bg-gray-900 border-gray-600 text-white"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRegisterModal(false)}
              className="bg-gray-900 hover:bg-gray-700 border-gray-600 text-white"
            >
              Cancel
            </Button>
            <Button
              onClick={handleRegister}
              disabled={isRegistering}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isRegistering ? 'Registering...' : 'Register'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
