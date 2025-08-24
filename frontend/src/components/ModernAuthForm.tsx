/**
 * Modern AuthForm component that switches between login and register
 */

import React, { useState } from 'react';
import { AuthLayout } from './AuthLayout';
import { LoginComponent } from './LoginComponent';
import { RegisterComponent } from './RegisterComponent';

interface AuthFormProps {
  mode: 'login' | 'register';
  onModeChange: (mode: 'login' | 'register') => void;
}

const ModernAuthForm: React.FC<AuthFormProps> = ({ mode: initialMode, onModeChange }) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);

  const handleModeChange = (newMode: 'login' | 'register') => {
    setMode(newMode);
    onModeChange(newMode);
  };

  const getTitle = () => {
    return mode === 'login' ? 'Welcome Back' : 'Create Your Account';
  };

  const getSubtitle = () => {
    return mode === 'login' 
      ? 'Sign in to access your personalized weather experience'
      : 'Join thousands of users who trust WeatherAI for accurate forecasts';
  };

  return (
    <AuthLayout title={getTitle()} subtitle={getSubtitle()}>
      {mode === 'login' ? (
        <LoginComponent onSwitchToRegister={() => handleModeChange('register')} />
      ) : (
        <RegisterComponent onSwitchToLogin={() => handleModeChange('login')} />
      )}
    </AuthLayout>
  );
};

export default ModernAuthForm;