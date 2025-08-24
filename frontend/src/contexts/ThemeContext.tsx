/**
 * Theme context for managing light/dark mode state.
 */

import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  effectiveTheme: 'light' | 'dark'; // The actual theme being applied
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Get saved theme from localStorage, default to 'system'
    const savedTheme = localStorage.getItem('theme') as Theme;
    return savedTheme || 'system';
  });

  // Get the effective theme (what's actually applied)
  const getEffectiveTheme = (theme: Theme): 'light' | 'dark' => {
    if (theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return theme;
  };

  const [effectiveTheme, setEffectiveTheme] = useState<'light' | 'dark'>(() => getEffectiveTheme(theme));

  // Update effective theme when system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = () => {
      if (theme === 'system') {
        setEffectiveTheme(getEffectiveTheme('system'));
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  // Apply theme classes to document
  useEffect(() => {
    const root = document.documentElement;
    
    // Remove all theme classes
    root.classList.remove('theme-light', 'theme-dark');
    
    // Add the appropriate theme class
    if (effectiveTheme === 'dark') {
      root.classList.add('theme-dark');
    } else {
      root.classList.add('theme-light');
    }
  }, [effectiveTheme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('theme', newTheme);
    setEffectiveTheme(getEffectiveTheme(newTheme));
  };

  const toggleTheme = () => {
    const newTheme = effectiveTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  const value: ThemeContextType = {
    theme,
    effectiveTheme,
    setTheme,
    toggleTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};