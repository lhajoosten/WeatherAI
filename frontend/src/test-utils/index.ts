// Test utilities for React components and hooks

import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, RenderOptions } from '@testing-library/react';
import React, { ReactElement } from 'react';

/**
 * Create a test query client with disabled retries and short cache times
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * Wrapper component that provides necessary providers for testing
 */
interface TestWrapperProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
}

function TestWrapper({ children, queryClient }: TestWrapperProps): React.ReactElement {
  const client = queryClient || createTestQueryClient();
  
  return React.createElement(
    ChakraProvider,
    { theme: extendTheme({}) },
    React.createElement(
      QueryClientProvider,
      { client },
      children
    )
  );
}

/**
 * Custom render function that includes providers
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
}

export function renderWithProviders(
  ui: ReactElement,
  options: CustomRenderOptions = {}
) {
  const { queryClient, ...renderOptions } = options;
  
  return render(ui, {
    wrapper: ({ children }) => React.createElement(TestWrapper, { queryClient, children }),
    ...renderOptions,
  });
}

// Re-export everything from testing library
export * from '@testing-library/react';
export { userEvent } from '@testing-library/user-event';

// Export the custom render as the default render
export { renderWithProviders as render };