import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Existing functional components
import Layout from '@/components/Layout';
import LocationGroupsView from '@/components/LocationGroupsView';
import LocationsView from '@/components/LocationsView';
import MapView from '@/components/MapView';
import ModernAuthForm from '@/components/ModernAuthForm';

// New feature pages (keep these for future development)
import { useAuth } from '@/contexts/AuthContext';
import RagPage from '@/features/rag/pages/RagPage';

// Auth context for authentication logic
import { UserManagement } from '@/features/user/pages';
import AnalyticsDashboard from '@/pages/AnalyticsDashboard';

// Route definitions - centralized for lazy loading preparation
export const routes = {
  auth: {
    login: '/auth/login',
  },
  locations: {
    index: '/locations',
  },
  groups: {
    index: '/groups',
  },
  map: {
    index: '/map',
  },
  analytics: {
    index: '/analytics',
  },
  rag: {
    index: '/rag',
  },
  user: {
    index: '/user',
  },
} as const;

/**
 * Authentication wrapper that shows login form for unauthenticated users
 * and the main app layout for authenticated users.
 */
const AuthenticatedApp: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <ModernAuthForm mode="login" onModeChange={() => {}} />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to={routes.locations.index} replace />} />
        <Route path={routes.locations.index} element={<LocationsView />} />
        <Route path={routes.groups.index} element={<LocationGroupsView />} />
        <Route path={routes.map.index} element={<MapView />} />
        <Route path={routes.analytics.index} element={<AnalyticsDashboard />} />
        <Route path={routes.rag.index} element={<RagPage />} />
        <Route path="/user/*" element={<UserManagement />} />
        <Route path="*" element={<Navigate to={routes.locations.index} replace />} />
      </Routes>
    </Layout>
  );
};

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
interface AppRoutesProps {
  // Future: isAuthenticated prop for conditional routing
}

/**
 * Main routing component that handles authentication flow.
 * Uses existing functional components while maintaining new architecture patterns.
 */
const AppRoutes: React.FC<AppRoutesProps> = () => {
  return <AuthenticatedApp />;
};

export default AppRoutes;