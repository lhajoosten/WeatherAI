import React, { ReactNode } from 'react';

import { I18nProvider } from '@/shared/i18n';

interface I18nWrapperProps {
  children: ReactNode;
}

/**
 * I18n provider wrapper for the application
 */
export const I18nWrapper: React.FC<I18nWrapperProps> = ({ children }) => {
  return (
    <I18nProvider>
      {children}
    </I18nProvider>
  );
};