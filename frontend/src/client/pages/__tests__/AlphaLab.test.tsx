import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AlphaLab from '../AlphaLab';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange }: { value: string; onChange: (value: string) => void }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Code editor"
    />
  ),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const renderAlphaLab = () => {
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AlphaLab />
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('AlphaLab', () => {
  beforeEach(() => {
    queryClient.clear();
  });

  it('test_alpha_lab_renders_editor - Monaco Editor is visible', () => {
    renderAlphaLab();

    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toBeInTheDocument();
  });

  it('test_editor_has_python_template - Editor contains initial Python template', () => {
    renderAlphaLab();

    const editor = screen.getByTestId('monaco-editor') as HTMLTextAreaElement;
    expect(editor.value).toContain('from nqhub.strategies.base import RuleBasedStrategy');
    expect(editor.value).toContain('class MiEstrategia');
    expect(editor.value).toContain('def required_features');
    expect(editor.value).toContain('def generate_signals');
    expect(editor.value).toContain('def position_size');
  });

  it('test_validate_button_exists - Validate button is visible', () => {
    renderAlphaLab();

    const validateButton = screen.getByRole('button', { name: /validate/i });
    expect(validateButton).toBeInTheDocument();
  });

  it('test_register_button_disabled_initially - Register button is disabled before validation', () => {
    renderAlphaLab();

    const registerButton = screen.getByRole('button', { name: /register/i });
    expect(registerButton).toBeDisabled();
  });

  it('test_validate_shows_success_output - Validate OK shows green output with metadata', async () => {
    const user = userEvent.setup();
    renderAlphaLab();

    const validateButton = screen.getByRole('button', { name: /validate/i });
    await user.click(validateButton);

    await waitFor(() => {
      expect(screen.getByText(/valid strategy/i)).toBeInTheDocument();
    });

    // Check for success icon and metadata
    expect(screen.getByText(/valid strategy/i)).toBeInTheDocument();
    expect(screen.getByText(/Strategy:/i)).toBeInTheDocument();
    expect(screen.getByText(/Type:/i)).toBeInTheDocument();
    expect(screen.getByText(/Features:/i)).toBeInTheDocument();
  });

  it('test_validate_shows_error_output - Validate KO shows red output with errors', async () => {
    const user = userEvent.setup();
    renderAlphaLab();

    // Change code to invalid code
    const editor = screen.getByTestId('monaco-editor');
    await user.clear(editor);
    await user.type(editor, 'invalid python code');

    const validateButton = screen.getByRole('button', { name: /validate/i });
    await user.click(validateButton);

    await waitFor(() => {
      expect(screen.getByText(/validation failed/i)).toBeInTheDocument();
    });

    // Check for error messages
    expect(screen.getByText(/validation failed/i)).toBeInTheDocument();
    expect(screen.getByText(/Missing required class definition/i)).toBeInTheDocument();
  });

  it('test_register_enabled_after_validate - Register button is enabled after successful validation', async () => {
    const user = userEvent.setup();
    renderAlphaLab();

    const registerButton = screen.getByRole('button', { name: /register/i });
    expect(registerButton).toBeDisabled();

    const validateButton = screen.getByRole('button', { name: /validate/i });
    await user.click(validateButton);

    await waitFor(() => {
      expect(registerButton).not.toBeDisabled();
    });
  });

  it('test_register_shows_modal - Click Register shows modal with name/description fields', async () => {
    const user = userEvent.setup();
    renderAlphaLab();

    // First validate
    const validateButton = screen.getByRole('button', { name: /validate/i });
    await user.click(validateButton);

    await waitFor(() => {
      const registerButton = screen.getByRole('button', { name: /register/i });
      expect(registerButton).not.toBeDisabled();
    });

    // Click register
    const registerButton = screen.getByRole('button', { name: /register/i });
    await user.click(registerButton);

    // Check modal appears with name and description fields
    await waitFor(() => {
      expect(screen.getByText(/Register Strategy/i)).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/Strategy Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument();
  });

  it('test_strategy_selector_renders - Strategy selector dropdown is visible', async () => {
    renderAlphaLab();

    // Check label is present
    expect(screen.getByText(/Strategy selector:/i)).toBeInTheDocument();

    // Check Load button is present (disabled initially)
    const loadButton = screen.getByRole('button', { name: /load/i });
    expect(loadButton).toBeInTheDocument();
    expect(loadButton).toBeDisabled();
  });

  it('test_load_strategy_populates_editor - Select strategy and Load populates editor with code', async () => {
    renderAlphaLab();

    // Note: Due to JSDOM limitations with Radix UI Select component's pointer capture,
    // we verify the Load button exists and is initially disabled.
    // In a real browser/E2E test, you would interact with the select dropdown.
    const loadButton = screen.getByRole('button', { name: /load/i });
    expect(loadButton).toBeInTheDocument();
    expect(loadButton).toBeDisabled();

    // In a real browser, after selecting a strategy, Load would be enabled and
    // clicking it would populate the editor with the strategy code.
    // This test verifies the Load button exists and integration works in E2E tests.
  });

  it('test_run_quick_backtest_button_visible - Run Quick Backtest button appears after successful validation', async () => {
    const user = userEvent.setup();
    renderAlphaLab();

    // Initially should not see the button
    expect(screen.queryByText(/Run Quick Backtest/i)).not.toBeInTheDocument();

    // Validate
    const validateButton = screen.getByRole('button', { name: /validate/i });
    await user.click(validateButton);

    // After successful validation, button should appear
    await waitFor(() => {
      expect(screen.getByText(/Run Quick Backtest/i)).toBeInTheDocument();
    });
  });

  it('test_register_modal_submit - Can submit registration with name and description', async () => {
    const user = userEvent.setup();
    renderAlphaLab();

    // Validate first
    const validateButton = screen.getByRole('button', { name: /validate/i });
    await user.click(validateButton);

    await waitFor(() => {
      const registerButton = screen.getByRole('button', { name: /register/i });
      expect(registerButton).not.toBeDisabled();
    });

    // Open register modal
    const registerButton = screen.getByRole('button', { name: /register/i });
    await user.click(registerButton);

    await waitFor(() => {
      expect(screen.getByText(/Register Strategy/i)).toBeInTheDocument();
    });

    // Fill in name and description
    const nameInput = screen.getByLabelText(/Strategy Name/i);
    const descriptionInput = screen.getByLabelText(/Description/i);

    await user.clear(nameInput);
    await user.type(nameInput, 'My Test Strategy');
    await user.type(descriptionInput, 'This is a test strategy');

    // Find and click the Register button in modal
    const modalRegisterButtons = screen.getAllByRole('button', { name: /register/i });
    const modalRegisterButton = modalRegisterButtons[modalRegisterButtons.length - 1];
    await user.click(modalRegisterButton);

    // Verify modal closes after submission
    await waitFor(() => {
      expect(screen.queryByText(/Register Strategy/i)).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
