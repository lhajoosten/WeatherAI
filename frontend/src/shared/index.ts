// Re-export all shared modules for convenient importing
export * from './api';
export * from './config';
export * from './i18n';
export * from './theme';
export * from './types';
export * from './ui';

// Export from lib with explicit names to avoid conflicts
export {
  fetchWithConfig,
  FetchError,
  logger as appLogger,
  delay,
  debounce,
  throttle,
  generateId,
  safeJsonParse,
} from './lib';

// Export observability with explicit names to avoid conflicts  
export {
  logger as devLogger,
  recordMetric,
  withTiming,
  useTrace,
} from './observability';