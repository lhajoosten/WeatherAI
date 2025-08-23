import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ChakraProvider, ColorModeScript, extendTheme } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { LocationProvider } from './context/LocationContext';
import AuthForm from './components/AuthForm';
import LocationsView from './components/LocationsView';
import LocationGroupsView from './components/LocationGroupsView';
import MapView from './components/MapView';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import Layout from './components/Layout';

// Create a custom theme
const theme = extendTheme({
  config: {
    initialColorMode: 'light',
    useSystemColorMode: false,
  },
  styles: {
    global: (props: any) => ({
      body: {
        bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
      },
    }),
  },
});

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

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
    return <AuthForm mode="login" onModeChange={() => {}} />;
  }

  return (
    <LocationProvider>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/locations" replace />} />
            <Route path="/locations" element={<LocationsView />} />
            <Route path="/groups" element={<LocationGroupsView />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/analytics" element={<AnalyticsDashboard />} />
            <Route path="*" element={<Navigate to="/locations" replace />} />
          </Routes>
        </Layout>
      </Router>
    </LocationProvider>
  );
};

const App: React.FC = () => {
  return (
    <>
      <ColorModeScript initialColorMode={theme.config.initialColorMode} />
      <ChakraProvider theme={theme}>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <AuthenticatedApp />
          </AuthProvider>
        </QueryClientProvider>
      </ChakraProvider>
    </>
  );
};

export default App;