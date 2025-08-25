// Shared utility functions - to be populated during migration

/**
 * Format a date string to a readable format
 */
export const formatDate = (date: string | Date): string => {
  // Placeholder implementation
  return new Date(date).toLocaleDateString();
};

/**
 * Debounce function to limit rapid successive calls
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  let timeoutId: ReturnType<typeof globalThis.setTimeout>;
  return (...args: Parameters<T>) => {
    globalThis.clearTimeout(timeoutId);
    timeoutId = globalThis.setTimeout(() => func(...args), delay);
  };
};

/**
 * Simple sleep utility for testing and animations
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise(resolve => globalThis.setTimeout(resolve, ms));
};

/**
 * Check if a value is empty (null, undefined, empty string, empty array)
 */
export const isEmpty = (value: any): boolean => {
  if (value == null) return true;
  if (typeof value === 'string') return value.length === 0;
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

export default {
  formatDate,
  debounce,
  sleep,
  isEmpty,
};