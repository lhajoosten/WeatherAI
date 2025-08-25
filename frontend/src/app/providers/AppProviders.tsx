import React, { ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { I18nWrapper } from './I18nProvider';
import { QueryProvider } from './QueryProvider';
import { ThemeProvider } from './ThemeProvider';

import { AuthProvider } from '@/core/auth/AuthContext';
import { ErrorBoundary } from '@/core/error/ErrorBoundary';

interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Composed application providers following the provider pattern.
 * Wraps the app with all necessary context providers in the correct order.
 * Order: Error Boundary -> I18n -> Theme -> Query -> Auth -> Router
 */
const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <ErrorBoundary>
      <I18nWrapper>
        <ThemeProvider>
          <QueryProvider>
            <AuthProvider>
              <BrowserRouter>
                {children}
              </BrowserRouter>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </I18nWrapper>
    </ErrorBoundary>
  );
};

export default AppProviders;