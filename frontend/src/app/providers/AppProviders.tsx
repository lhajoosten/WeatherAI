import React, { ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { I18nWrapper } from './I18nProvider';
import { QueryProvider } from './QueryProvider';
import { ThemeProvider } from './ThemeProvider';

// Use existing functional contexts instead of placeholder ones
import { LocationProvider } from '@/context/LocationContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider as LegacyThemeProvider } from '@/contexts/ThemeContext';
import { ErrorBoundary } from '@/core/error/ErrorBoundary';

interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Composed application providers following the provider pattern.
 * Wraps the app with all necessary context providers in the correct order.
 * Order: Error Boundary -> I18n -> Theme -> Query -> Auth -> Location -> Router
 * 
 * Note: Using existing functional contexts (AuthProvider, LocationProvider)
 * from the previous architecture while maintaining the new provider composition pattern.
 */
const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <ErrorBoundary>
      <I18nWrapper>
        <ThemeProvider>
          <LegacyThemeProvider>
            <QueryProvider>
              <AuthProvider>
                <LocationProvider>
                  <BrowserRouter>
                    {children}
                  </BrowserRouter>
                </LocationProvider>
              </AuthProvider>
            </QueryProvider>
          </LegacyThemeProvider>
        </ThemeProvider>
      </I18nWrapper>
    </ErrorBoundary>
  );
};

export default AppProviders;