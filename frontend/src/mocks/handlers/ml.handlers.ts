import { http, HttpResponse } from 'msw';

const API_BASE = '/api/v1';

// Mock models database
const mockModels = [
  {
    id: 'model-1',
    name: 'ICT_FVG_Classifier_v3',
    version: '3.2.1',
    type: 'MLStrategy',
    framework: 'xgboost',
    sharpe_ratio: 1.87,
    win_rate: 64.2,
    max_drawdown: 12.4,
    huggingface_repo: 'carrilloric/nq-fvg-v3',
    wandb_run_url: 'https://wandb.ai/nqhub/fvg-classifier/runs/xyz123',
    status: 'deployed',
    registered_at: '2026-03-15T10:30:00Z',
  },
  {
    id: 'model-2',
    name: 'OrderBlock_XGBoost_v2',
    version: '2.1.0',
    type: 'MLStrategy',
    framework: 'xgboost',
    sharpe_ratio: 2.14,
    win_rate: 68.5,
    max_drawdown: 9.8,
    huggingface_repo: 'carrilloric/nq-ob-v2',
    wandb_run_url: 'https://wandb.ai/nqhub/orderblock/runs/abc456',
    status: 'available',
    registered_at: '2026-03-20T14:15:00Z',
  },
  {
    id: 'model-3',
    name: 'PPO_ICT_Agent_v1',
    version: '1.0.0',
    type: 'RLStrategy',
    framework: 'pytorch',
    sharpe_ratio: 1.65,
    win_rate: 61.3,
    max_drawdown: 15.2,
    wandb_run_url: 'https://wandb.ai/nqhub/ppo-agent/runs/def789',
    status: 'available',
    registered_at: '2026-03-18T09:00:00Z',
  },
];

// Mock datasets database
const mockDatasets = [
  {
    id: 'dataset-1',
    name: 'NQ_2024_1min_oflow',
    timeframe: '1min',
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    row_count: 322540,
    size_mb: 847,
    gcs_path: 'gs://nqhub-datasets/nq_2024_1min_oflow',
    signed_url: 'https://storage.googleapis.com/nqhub-datasets/nq_2024_1min_oflow?signed_token=xyz',
    exported_at: '2026-03-10T08:30:00Z',
    has_orderflow: true,
  },
  {
    id: 'dataset-2',
    name: 'NQ_2023_5min_basic',
    timeframe: '5min',
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    row_count: 64508,
    size_mb: 124,
    gcs_path: 'gs://nqhub-datasets/nq_2023_5min_basic',
    signed_url: 'https://storage.googleapis.com/nqhub-datasets/nq_2023_5min_basic?signed_token=abc',
    exported_at: '2026-03-08T12:00:00Z',
    has_orderflow: false,
  },
];

// Mock experiments database
const mockExperiments = [
  {
    id: 'exp-1',
    run_name: 'run_20260315_ppo_v4',
    algorithm: 'PPO',
    episodes: 50000,
    final_reward: 2.847,
    sharpe: 1.65,
    status: 'completed',
    wandb_url: 'https://wandb.ai/nqhub/rl-experiments/runs/run123',
    created_at: '2026-03-15T10:00:00Z',
  },
  {
    id: 'exp-2',
    run_name: 'run_20260318_sac_v2',
    algorithm: 'SAC',
    episodes: 30000,
    final_reward: 2.123,
    sharpe: 1.42,
    status: 'completed',
    wandb_url: 'https://wandb.ai/nqhub/rl-experiments/runs/run456',
    created_at: '2026-03-18T14:30:00Z',
  },
  {
    id: 'exp-3',
    run_name: 'run_20260320_ppo_v5',
    algorithm: 'PPO',
    episodes: 25000,
    final_reward: 1.876,
    sharpe: 1.28,
    status: 'running',
    wandb_url: 'https://wandb.ai/nqhub/rl-experiments/runs/run789',
    created_at: '2026-03-20T09:15:00Z',
  },
];

export const mlHandlers = [
  // Get all models
  http.get(`${API_BASE}/ml/models`, () => {
    return HttpResponse.json({
      models: mockModels,
      count: mockModels.length,
    });
  }),

  // Deploy a model
  http.post(`${API_BASE}/ml/models/:id/deploy`, ({ params }) => {
    const { id } = params;
    const model = mockModels.find((m) => m.id === id);

    if (!model) {
      return HttpResponse.json(
        { error: 'Model not found' },
        { status: 404 }
      );
    }

    if (model.status !== 'available') {
      return HttpResponse.json(
        { error: 'Only available models can be deployed' },
        { status: 400 }
      );
    }

    // Update model status
    model.status = 'deployed';

    return HttpResponse.json({
      id: model.id,
      status: 'deployed',
      message: 'Model deployed successfully',
    });
  }),

  // Get all datasets
  http.get(`${API_BASE}/ml/datasets`, () => {
    return HttpResponse.json({
      datasets: mockDatasets,
      count: mockDatasets.length,
    });
  }),

  // Get all experiments
  http.get(`${API_BASE}/ml/experiments`, () => {
    return HttpResponse.json({
      experiments: mockExperiments,
      count: mockExperiments.length,
    });
  }),

  // Legacy endpoints
  http.post(`${API_BASE}/ml/train`, () => HttpResponse.json({ id: 'model-1', status: 'training' })),
  http.post(`${API_BASE}/ml/predict`, () => HttpResponse.json({ prediction: 1, confidence: 0.85 })),
];