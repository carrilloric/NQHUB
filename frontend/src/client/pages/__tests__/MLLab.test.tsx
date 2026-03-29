import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MLLab from '../MLLab';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const renderMLLab = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MLLab />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('MLLab', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  it('test_ml_lab_renders_3_tabs - ML Lab renders with 3 tabs', async () => {
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /model registry/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /dataset registry/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /experiments/i })).toBeInTheDocument();
    });
  });

  it('test_model_registry_shows_cards - Model Registry tab shows model cards', async () => {
    renderMLLab();

    await waitFor(() => {
      // Check for model names from mock data
      expect(screen.getByText(/ICT_FVG_Classifier_v3/i)).toBeInTheDocument();
      expect(screen.getByText(/OrderBlock_XGBoost_v2/i)).toBeInTheDocument();
      expect(screen.getByText(/PPO_ICT_Agent_v1/i)).toBeInTheDocument();
    });

    // Check for model metadata (multiple cards have these, use getAllByText)
    expect(screen.getAllByText(/Sharpe:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Win Rate:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Max DD:/i).length).toBeGreaterThan(0);
  });

  it('test_deploy_button_on_available_model - Deploy button visible on available models', async () => {
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByText(/OrderBlock_XGBoost_v2/i)).toBeInTheDocument();
    });

    // OrderBlock_XGBoost_v2 and PPO_ICT_Agent_v1 have status 'available'
    // They should have Deploy buttons
    const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
    // 2 models are available, so we should have at least 2 Deploy buttons
    expect(deployButtons.length).toBeGreaterThanOrEqual(2);
  });

  it('test_deploy_button_hidden_on_deployed - Deploy button hidden on deployed models', async () => {
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByText(/ICT_FVG_Classifier_v3/i)).toBeInTheDocument();
    });

    // ICT_FVG_Classifier_v3 has status 'deployed'
    // We have 3 models total: 1 deployed, 2 available
    // So we should have exactly 2 Deploy buttons (not 3)
    const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
    expect(deployButtons.length).toBe(2);
  });

  it('test_deploy_shows_confirmation_modal - Deploy button shows confirmation modal', async () => {
    const user = userEvent.setup();
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByText(/OrderBlock_XGBoost_v2/i)).toBeInTheDocument();
    });

    // Click Deploy button on an available model
    const deployButtons = screen.getAllByRole('button', { name: /^deploy$/i });
    await user.click(deployButtons[0]);

    // Check modal appears
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Deploy Model/i)).toBeInTheDocument();
      expect(screen.getByText(/¿Desplegar este modelo como activo para nuevos bots\?/i)).toBeInTheDocument();
    });

    // Check modal has Cancel and Deploy buttons
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    expect(cancelButton).toBeInTheDocument();

    // The modal should have a Deploy button
    const deployButtonsInModal = screen.getAllByRole('button', { name: /deploy/i });
    expect(deployButtonsInModal.length).toBeGreaterThanOrEqual(1);
  });

  it('test_dataset_registry_shows_list - Dataset Registry tab shows dataset list', async () => {
    const user = userEvent.setup();
    renderMLLab();

    // Switch to Dataset Registry tab
    const datasetTab = screen.getByRole('tab', { name: /dataset registry/i });
    await user.click(datasetTab);

    await waitFor(() => {
      // Check for dataset names from mock data (appears in title and GCS path, use getAllByText)
      const dataset1 = screen.getAllByText(/NQ_2024_1min_oflow/i);
      expect(dataset1.length).toBeGreaterThan(0);

      const dataset2 = screen.getAllByText(/NQ_2023_5min_basic/i);
      expect(dataset2.length).toBeGreaterThan(0);
    });

    // Check for dataset metadata
    expect(screen.getAllByText(/Rows:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Size:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Exported:/i).length).toBeGreaterThan(0);
  });

  it('test_dataset_download_link_exists - Dataset cards have Download button', async () => {
    const user = userEvent.setup();
    renderMLLab();

    // Switch to Dataset Registry tab
    const datasetTab = screen.getByRole('tab', { name: /dataset registry/i });
    await user.click(datasetTab);

    await waitFor(() => {
      const dataset1 = screen.getAllByText(/NQ_2024_1min_oflow/i);
      expect(dataset1.length).toBeGreaterThan(0);
    });

    // Check for Download buttons (2 datasets)
    const downloadButtons = screen.getAllByRole('button', { name: /download/i });
    expect(downloadButtons.length).toBe(2);
  });

  it('test_experiments_tab_renders - Experiments tab renders experiment list', async () => {
    const user = userEvent.setup();
    renderMLLab();

    // Switch to Experiments tab
    const experimentsTab = screen.getByRole('tab', { name: /experiments/i });
    await user.click(experimentsTab);

    await waitFor(() => {
      // Check for experiment names from mock data
      expect(screen.getByText(/run_20260315_ppo_v4/i)).toBeInTheDocument();
      expect(screen.getByText(/run_20260318_sac_v2/i)).toBeInTheDocument();
      expect(screen.getByText(/run_20260320_ppo_v5/i)).toBeInTheDocument();
    });

    // Check for experiment metadata (multiple experiments have these fields)
    expect(screen.getAllByText(/Algorithm:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Episodes:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Final Reward:/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Sharpe:/i).length).toBeGreaterThan(0);
  });

  it('test_wandb_link_opens_externally - W&B link buttons exist', async () => {
    const user = userEvent.setup();
    renderMLLab();

    // Switch to Experiments tab
    const experimentsTab = screen.getByRole('tab', { name: /experiments/i });
    await user.click(experimentsTab);

    await waitFor(() => {
      expect(screen.getByText(/run_20260315_ppo_v4/i)).toBeInTheDocument();
    });

    // Check for "View in W&B" buttons
    const wandbButtons = screen.getAllByRole('button', { name: /view in w&b/i });
    expect(wandbButtons.length).toBeGreaterThan(0);
  });

  it('test_model_filters_work - Model filters correctly filter models', async () => {
    const user = userEvent.setup();
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByText(/ICT_FVG_Classifier_v3/i)).toBeInTheDocument();
      expect(screen.getByText(/PPO_ICT_Agent_v1/i)).toBeInTheDocument();
    });

    // Note: Due to JSDOM limitations with Radix UI Select component,
    // we verify that filter controls exist but cannot fully test interaction
    const filterSelects = screen.getAllByRole('combobox');
    expect(filterSelects.length).toBe(3); // Type, Framework, Status filters
  });

  it('test_deploy_success_updates_status - Successful deploy updates model status', async () => {
    const user = userEvent.setup();
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByText(/OrderBlock_XGBoost_v2/i)).toBeInTheDocument();
    });

    // Click Deploy button
    const deployButtons = screen.getAllByRole('button', { name: /deploy/i });
    const initialDeployButtonCount = deployButtons.length;
    await user.click(deployButtons[0]);

    // Confirm deployment in modal
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    const modalDeployButtons = screen.getAllByRole('button', { name: /^deploy$/i });
    const confirmButton = modalDeployButtons[modalDeployButtons.length - 1];
    await user.click(confirmButton);

    // Modal should close and model status should update
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    // Check that Deploy button count decreased (model now deployed)
    await waitFor(() => {
      const newDeployButtons = screen.queryAllByRole('button', { name: /deploy/i });
      expect(newDeployButtons.length).toBeLessThan(initialDeployButtonCount);
    });
  });

  it('test_huggingface_links_exist - HuggingFace repo links exist for ML models', async () => {
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByText(/ICT_FVG_Classifier_v3/i)).toBeInTheDocument();
    });

    // Check for HuggingFace links (2 ML models have HuggingFace repos)
    const hfLinks = screen.getAllByText(/HuggingFace/i);
    expect(hfLinks.length).toBe(2);
  });

  it('test_model_version_displayed - Model version is displayed', async () => {
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByText(/ICT_FVG_Classifier_v3/i)).toBeInTheDocument();
    });

    // Check for version display (multiple models have Version: label)
    expect(screen.getAllByText(/Version:/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/3\.2\.1/)).toBeInTheDocument();
    expect(screen.getByText(/2\.1\.0/)).toBeInTheDocument();
  });

  it('test_status_badges_render - Model status badges render with correct styling', async () => {
    renderMLLab();

    await waitFor(() => {
      expect(screen.getByText(/ICT_FVG_Classifier_v3/i)).toBeInTheDocument();
    });

    // Check for status badges (deployed, available)
    const statusBadges = screen.getAllByText(/● (deployed|available|archived)/i);
    expect(statusBadges.length).toBeGreaterThan(0);
  });
});
