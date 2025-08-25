import i18n from 'i18next';
import React, { createContext, useContext, useState, ReactNode } from 'react';
import { initReactI18next, useTranslation } from 'react-i18next';

import enTranslations from './locales/en.json';
import nlTranslations from './locales/nl.json';

import { getConfig } from '@/shared/config';

// Initialize i18next
i18n.use(initReactI18next).init({
  resources: {
    en: { translation: enTranslations },
    nl: { translation: nlTranslations },
  },
  lng: getConfig().DEFAULT_LOCALE,
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false, // React already escapes values
  },
});

interface I18nContextType {
  locale: string;
  setLocale: (locale: string) => void;
  t: (key: string, options?: any) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const useI18n = () => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};

export const useT = () => {
  const { t } = useTranslation();
  return t;
};

interface I18nProviderProps {
  children: ReactNode;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({ children }) => {
  const [locale, setLocaleState] = useState(i18n.language);
  const { t } = useTranslation();

  const setLocale = (newLocale: string) => {
    i18n.changeLanguage(newLocale);
    setLocaleState(newLocale);
    localStorage.setItem('locale', newLocale);
  };

  // Load saved locale on mount
  React.useEffect(() => {
    const savedLocale = localStorage.getItem('locale');
    if (savedLocale && savedLocale !== locale) {
      setLocale(savedLocale);
    }
  }, [locale]);

  const value: I18nContextType = {
    locale,
    setLocale,
    t,
  };

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
};

export { i18n };
export default i18n;