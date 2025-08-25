// Re-export all shared modules for convenient importing
export * from './config';
export * from './i18n';
export * from './theme';
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

// Export api and types separately to avoid conflicts
export * from './api';
export * from './types';