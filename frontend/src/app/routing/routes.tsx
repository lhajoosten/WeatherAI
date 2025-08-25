import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Feature pages
import AnalyticsPage from '@/features/analytics/pages/AnalyticsPage';
import LoginPage from '@/features/auth/pages/LoginPage';
import DigestPage from '@/features/digest/pages/DigestPage';
import LocationsPage from '@/features/locations/pages/LocationsPage';
import RagPage from '@/features/rag/pages/RagPage';

// Route definitions - centralized for lazy loading preparation
export const routes = {
  auth: {
    login: '/auth/login',
  },
  locations: {
    index: '/locations',
  },
  digest: {
    index: '/digest',
  },
  analytics: {
    index: '/analytics',
  },
  rag: {
    index: '/rag',
  },
} as const;

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
interface AppRoutesProps {
  // Future: isAuthenticated prop for conditional routing
}

const AppRoutes: React.FC<AppRoutesProps> = () => {
  return (
    <Routes>
      {/* Default redirect to locations */}
      <Route path="/" element={<Navigate to={routes.locations.index} replace />} />
      
      {/* Auth routes */}
      <Route path={routes.auth.login} element={<LoginPage />} />
      
      {/* Feature routes */}
      <Route path={routes.locations.index} element={<LocationsPage />} />
      <Route path={routes.digest.index} element={<DigestPage />} />
      <Route path={routes.analytics.index} element={<AnalyticsPage />} />
      <Route path={routes.rag.index} element={<RagPage />} />
      
      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to={routes.locations.index} replace />} />
    </Routes>
  );
};

export default AppRoutes;