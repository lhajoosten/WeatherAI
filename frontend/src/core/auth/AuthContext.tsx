import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

import { httpClient } from '@/shared/api';

// Placeholder types - to be moved to @/types when migrating business logic
interface User {
  id: number;
  email: string;
  timezone: string;
  created_at: string;
}

interface UserLogin {
  email: string;
  password: string;
}

interface UserCreate {
  email: string;
  password: string;
  timezone?: string;
}

interface TokenResponse { access_token: string; token_type?: string; user: User }

interface AuthContextType {
  user: User | null;
  login: (credentials: UserLogin) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on app load
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Failed to parse saved user:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (credentials: UserLogin) => {
    setLoading(true);
    try {
      const response = await httpClient.post<TokenResponse>('/auth/login', credentials);
      if (response?.access_token && response?.user) {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        setUser(response.user);
      } else {
        throw new Error('Invalid login response');
      }
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: UserCreate) => {
    setLoading(true);
    try {
      const response = await httpClient.post<TokenResponse>('/auth/register', userData);
      if (response?.access_token && response?.user) {
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('user', JSON.stringify(response.user));
        setUser(response.user);
      } else {
        throw new Error('Invalid register response');
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthProvider;