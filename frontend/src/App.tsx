import React from 'react';

import AppProviders from '@/app/providers/AppProviders';
import AppRoutes from '@/app/routing/routes';

/**
 * Main application component using the new modular architecture.
 * 
 * This is the new entry point that composes providers and routing
 * in a clean, feature-first structure.
 */
const App: React.FC = () => {
  return (
    <AppProviders>
      <AppRoutes />
    </AppProviders>
  );
};

export default App;