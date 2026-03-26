/**
 * Machine Learning Types
 */

export interface MLModel {
  id: string;
  name: string;
  type: 'classification' | 'regression' | 'reinforcement';
  algorithm: string;
  version: string;
  status: 'training' | 'ready' | 'deployed' | 'deprecated';
  accuracy?: number;
  features: string[];
  target: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface TrainModelRequest {
  name: string;
  algorithm: string;
  features: string[];
  target: string;
  train_start_date: string;
  train_end_date: string;
  validation_split: number;
  hyperparameters?: Record<string, any>;
}

export interface PredictRequest {
  model_id: string;
  features: Record<string, number>;
  timestamp?: string;
}

export interface PredictResponse {
  model_id: string;
  prediction: number | string;
  confidence?: number;
  feature_importance?: Record<string, number>;
  timestamp: string;
}

export interface ModelMetrics {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  rmse?: number;
  mae?: number;
  confusion_matrix?: number[][];
}