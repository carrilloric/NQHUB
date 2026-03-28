/**
 * Approval Workflow Types
 */

export interface ApprovalChecklist {
  strategy_id: string;
  items: ChecklistItem[];
  overall_score: number;
  recommendation: 'approve' | 'review' | 'reject';
  created_at: string;
}

export interface ChecklistItem {
  id: string;
  category: 'performance' | 'risk' | 'implementation' | 'compliance';
  name: string;
  description: string;
  status: 'pass' | 'fail' | 'warning' | 'not_applicable';
  score: number;
  max_score: number;
  details?: string;
}

export interface ApprovalSubmission {
  strategy_id: string;
  checklist_items: Record<string, boolean>;
  risk_assessment: RiskAssessment;
  backtest_report: string;
  forward_test_results?: string;
  comments: string;
}

export interface RiskAssessment {
  max_drawdown_acceptable: boolean;
  position_sizing_appropriate: boolean;
  stop_loss_implemented: boolean;
  correlation_checked: boolean;
  stress_tested: boolean;
  risk_reward_ratio: number;
}

export interface ApprovalDecision {
  strategy_id: string;
  decision: 'approved' | 'rejected' | 'conditional';
  conditions?: string[];
  reviewer_comments: string;
  approved_for: 'paper' | 'limited_live' | 'full_live';
  expiry_date?: string;
}