// Utility functions for common operations

/**
 * Create a delay for async operations
 * @param ms - Milliseconds to delay
 * @returns Promise that resolves after the delay
 */
export const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

/**
 * Debounce function calls
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds
 * @returns Debounced function
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: ReturnType<typeof setTimeout>;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(null, args), wait);
  };
};

/**
 * Throttle function calls
 * @param func - Function to throttle  
 * @param limit - Time limit in milliseconds
 * @returns Throttled function
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func.apply(null, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * Generate a unique ID
 * @returns Random unique identifier
 */
export const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Safe JSON parsing with fallback
 * @param str - String to parse
 * @param fallback - Fallback value if parsing fails
 * @returns Parsed object or fallback
 */
export const safeJsonParse = <T = unknown>(str: string, fallback: T = null as T): T => {
  try {
    return JSON.parse(str) as T;
  } catch {
    return fallback;
  }
};

/**
 * Safe JSON stringification
 * @param obj - Object to stringify
 * @param fallback - Fallback string if stringification fails
 * @returns JSON string or fallback
 */
export const safeJsonStringify = (obj: unknown, fallback = '{}'): string => {
  try {
    return JSON.stringify(obj);
  } catch {
    return fallback;
  }
};

/**
 * Check if a value is not null or undefined
 * @param value - Value to check
 * @returns Type guard for non-null values
 */
export const isNotNullish = <T>(value: T | null | undefined): value is T => {
  return value !== null && value !== undefined;
};

/**
 * Create a promise that can be resolved/rejected externally
 * @returns Object with promise and control functions
 */
export const createDeferredPromise = <T = void>() => {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: any) => void;
  
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  
  return { promise, resolve, reject };
};

/**
 * Clamp a number between min and max values
 * @param value - Value to clamp
 * @param min - Minimum value
 * @param max - Maximum value
 * @returns Clamped value
 */
export const clamp = (value: number, min: number, max: number): number => {
  return Math.min(Math.max(value, min), max);
};

/**
 * Format bytes to human readable string
 * @param bytes - Bytes to format
 * @param decimals - Number of decimal places
 * @returns Formatted string
 */
export const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Simple hash function for strings (for non-cryptographic use)
 * @param str - String to hash
 * @returns Hash number
 */
export const simpleHash = (str: string): number => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash;
};

/**
 * Cryptographic SHA-256 hash (requires crypto API)
 * @param text - Text to hash
 * @returns Promise resolving to hex hash string
 */
export const sha256Hash = async (text: string): Promise<string> => {
  if (!crypto?.subtle) {
    throw new Error('crypto.subtle not available');
  }
  
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return hashHex;
};