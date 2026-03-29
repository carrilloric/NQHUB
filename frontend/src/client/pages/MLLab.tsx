import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Play, ExternalLink, Download, CheckCircle2 } from 'lucide-react';

interface Model {
  id: string;
  name: string;
  version: string;
  type: 'MLStrategy' | 'RLStrategy';
  framework: string;
  sharpe_ratio: number;
  win_rate: number;
  max_drawdown: number;
  huggingface_repo?: string;
  wandb_run_url?: string;
  status: 'available' | 'deployed' | 'archived';
  registered_at: string;
}

interface Dataset {
  id: string;
  name: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  row_count: number;
  size_mb: number;
  gcs_path: string;
  signed_url: string;
  exported_at: string;
  has_orderflow: boolean;
}

interface Experiment {
  id: string;
  run_name: string;
  algorithm: string;
  episodes: number;
  final_reward: number;
  sharpe: number;
  status: 'completed' | 'running' | 'failed';
  wandb_url: string;
  created_at: string;
}

export default function MLLab() {
  const [models, setModels] = useState<Model[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [frameworkFilter, setFrameworkFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const { toast } = useToast();

  // Load models on mount
  useState(() => {
    fetch('/api/v1/ml/models')
      .then((res) => res.json())
      .then((data) => setModels(data.models || []))
      .catch((err) => console.error('Failed to load models:', err));
  });

  // Load datasets on mount
  useState(() => {
    fetch('/api/v1/ml/datasets')
      .then((res) => res.json())
      .then((data) => setDatasets(data.datasets || []))
      .catch((err) => console.error('Failed to load datasets:', err));
  });

  // Load experiments on mount
  useState(() => {
    fetch('/api/v1/ml/experiments')
      .then((res) => res.json())
      .then((data) => setExperiments(data.experiments || []))
      .catch((err) => console.error('Failed to load experiments:', err));
  });

  const handleDeployClick = (model: Model) => {
    setSelectedModel(model);
    setShowDeployModal(true);
  };

  const handleDeployConfirm = async () => {
    if (!selectedModel) return;

    setIsDeploying(true);
    try {
      const response = await fetch(`/api/v1/ml/models/${selectedModel.id}/deploy`, {
        method: 'POST',
      });

      if (response.ok) {
        // Update model status locally
        setModels((prev) =>
          prev.map((m) =>
            m.id === selectedModel.id ? { ...m, status: 'deployed' as const } : m
          )
        );

        toast({
          title: 'Success',
          description: 'Modelo desplegado correctamente',
        });
        setShowDeployModal(false);
        setSelectedModel(null);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to deploy model',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to deploy model',
        variant: 'destructive',
      });
    } finally {
      setIsDeploying(false);
    }
  };

  const getStatusBadge = (status: Model['status']) => {
    const variants = {
      available: 'default',
      deployed: 'secondary',
      archived: 'outline',
    };
    const colors = {
      available: 'text-green-600',
      deployed: 'text-blue-600',
      archived: 'text-gray-600',
    };
    return (
      <Badge variant={variants[status] as any} className={colors[status]}>
        ● {status}
      </Badge>
    );
  };

  const getExperimentStatusBadge = (status: Experiment['status']) => {
    const icons = {
      completed: <CheckCircle2 className="w-4 h-4 text-green-600" />,
      running: <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />,
      failed: <span className="text-red-600">✗</span>,
    };
    return icons[status];
  };

  const filteredModels = models.filter((model) => {
    if (typeFilter !== 'all' && model.type !== typeFilter) return false;
    if (frameworkFilter !== 'all' && model.framework !== frameworkFilter) return false;
    if (statusFilter !== 'all' && model.status !== statusFilter) return false;
    return true;
  });

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">ML LAB</h1>

      <Tabs defaultValue="models" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="models">Model Registry</TabsTrigger>
          <TabsTrigger value="datasets">Dataset Registry</TabsTrigger>
          <TabsTrigger value="experiments">Experiments</TabsTrigger>
        </TabsList>

        {/* Tab 1: Model Registry */}
        <TabsContent value="models" className="space-y-4">
          {/* Filters */}
          <div className="flex gap-4 mb-4">
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="MLStrategy">ML Strategy</SelectItem>
                <SelectItem value="RLStrategy">RL Strategy</SelectItem>
              </SelectContent>
            </Select>

            <Select value={frameworkFilter} onValueChange={setFrameworkFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by framework" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Frameworks</SelectItem>
                <SelectItem value="xgboost">XGBoost</SelectItem>
                <SelectItem value="pytorch">PyTorch</SelectItem>
                <SelectItem value="onnx">ONNX</SelectItem>
              </SelectContent>
            </Select>

            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="available">Available</SelectItem>
                <SelectItem value="deployed">Deployed</SelectItem>
                <SelectItem value="archived">Archived</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Model Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredModels.map((model) => (
              <Card key={model.id} className="relative">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{model.name}</CardTitle>
                      <CardDescription>
                        {model.type} ({model.framework})
                      </CardDescription>
                    </div>
                    {model.status === 'available' && (
                      <Button
                        onClick={() => handleDeployClick(model)}
                        size="sm"
                        className="ml-2"
                      >
                        <Play className="w-4 h-4 mr-1" />
                        Deploy
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="text-sm">
                    <span className="text-gray-500">Version:</span> {model.version}
                  </div>
                  <div className="text-sm space-y-1">
                    <div>
                      <span className="text-gray-500">Sharpe:</span> {model.sharpe_ratio.toFixed(2)}
                    </div>
                    <div>
                      <span className="text-gray-500">Win Rate:</span> {model.win_rate.toFixed(1)}%
                    </div>
                    <div>
                      <span className="text-gray-500">Max DD:</span> {model.max_drawdown.toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    Registered: {new Date(model.registered_at).toLocaleDateString()}
                  </div>
                  {model.huggingface_repo && (
                    <a
                      href={`https://huggingface.co/${model.huggingface_repo}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                    >
                      HuggingFace <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  {model.wandb_run_url && (
                    <a
                      href={model.wandb_run_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                    >
                      W&B Run <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  <div className="pt-2">{getStatusBadge(model.status)}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredModels.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No models found matching your filters
            </div>
          )}
        </TabsContent>

        {/* Tab 2: Dataset Registry */}
        <TabsContent value="datasets" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {datasets.map((dataset) => (
              <Card key={dataset.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{dataset.name}</CardTitle>
                      <CardDescription>
                        {dataset.timeframe} | {dataset.start_date} to {dataset.end_date}
                      </CardDescription>
                    </div>
                    <Button
                      onClick={() => window.open(dataset.signed_url, '_blank')}
                      variant="outline"
                      size="sm"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Download
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex gap-8 text-sm">
                    <div>
                      <span className="text-gray-500">Rows:</span> {dataset.row_count.toLocaleString()}
                    </div>
                    <div>
                      <span className="text-gray-500">Size:</span> {dataset.size_mb} MB
                    </div>
                    {dataset.has_orderflow && (
                      <Badge variant="secondary">Includes Orderflow</Badge>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">
                    Exported: {new Date(dataset.exported_at).toLocaleDateString()}
                  </div>
                  <div className="text-xs font-mono text-gray-400 bg-gray-50 p-2 rounded">
                    {dataset.gcs_path}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {datasets.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No datasets available
            </div>
          )}
        </TabsContent>

        {/* Tab 3: Experiments (W&B) */}
        <TabsContent value="experiments" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {experiments.map((exp) => (
              <Card key={exp.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        {exp.run_name}
                        {getExperimentStatusBadge(exp.status)}
                      </CardTitle>
                      <CardDescription>
                        Algorithm: {exp.algorithm} | Episodes: {exp.episodes.toLocaleString()}
                      </CardDescription>
                    </div>
                    <Button
                      onClick={() => window.open(exp.wandb_url, '_blank')}
                      variant="outline"
                      size="sm"
                    >
                      View in W&B <ExternalLink className="w-4 h-4 ml-1" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex gap-8 text-sm">
                    <div>
                      <span className="text-gray-500">Final Reward:</span> {exp.final_reward.toFixed(3)}
                    </div>
                    <div>
                      <span className="text-gray-500">Sharpe:</span> {exp.sharpe.toFixed(2)}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    Created: {new Date(exp.created_at).toLocaleDateString()}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {experiments.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No experiments found
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Deploy Confirmation Modal */}
      <Dialog open={showDeployModal} onOpenChange={setShowDeployModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Deploy Model</DialogTitle>
            <DialogDescription>
              ¿Desplegar este modelo como activo para nuevos bots?
            </DialogDescription>
          </DialogHeader>
          {selectedModel && (
            <div className="py-4 space-y-2">
              <div className="font-semibold">{selectedModel.name}</div>
              <div className="text-sm text-gray-500">Version: {selectedModel.version}</div>
              <div className="text-sm text-gray-500">
                Sharpe: {selectedModel.sharpe_ratio.toFixed(2)} | Win Rate: {selectedModel.win_rate.toFixed(1)}%
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeployModal(false)}
              disabled={isDeploying}
            >
              Cancel
            </Button>
            <Button onClick={handleDeployConfirm} disabled={isDeploying}>
              {isDeploying ? 'Deploying...' : 'Deploy'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
