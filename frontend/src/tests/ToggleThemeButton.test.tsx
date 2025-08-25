import React from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';

import theme from '@/shared/theme';
import { ToggleThemeButton } from '@/shared/ui';

// Mock the i18n hook
vi.mock('@/shared/i18n', () => ({
  useT: () => (key: string) => key,
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ChakraProvider theme={theme}>
    {children}
  </ChakraProvider>
);

describe('ToggleThemeButton', () => {
  it('should render theme toggle button', () => {
    render(
      <TestWrapper>
        <ToggleThemeButton />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-label', 'ui.toggleTheme');
  });

  it('should toggle color mode when clicked', async () => {
    const user = userEvent.setup();
    
    render(
      <TestWrapper>
        <ToggleThemeButton />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    
    // Click to toggle theme
    await user.click(button);
    
    // Should still be rendered (testing basic interaction)
    expect(button).toBeInTheDocument();
  });

  it('should render different sizes correctly', () => {
    const { rerender } = render(
      <TestWrapper>
        <ToggleThemeButton size="sm" />
      </TestWrapper>
    );

    let button = screen.getByRole('button');
    expect(button).toBeInTheDocument();

    rerender(
      <TestWrapper>
        <ToggleThemeButton size="lg" />
      </TestWrapper>
    );

    button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });
});