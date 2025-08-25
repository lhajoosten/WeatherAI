// Client-side hashing utilities for logs and caching

/**
 * Create SHA-256 hash of text using Web Crypto API
 * @param text - Text to hash
 * @returns Promise resolving to hex hash string
 */
export async function sha256(text: string): Promise<string> {
  if (!crypto?.subtle) {
    throw new Error('Web Crypto API not available');
  }
  
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  
  return hashHex;
}

/**
 * Create a short hash for logging purposes (first 8 chars of SHA-256)
 * @param text - Text to hash
 * @returns Promise resolving to short hash string
 */
export async function shortHash(text: string): Promise<string> {
  const fullHash = await sha256(text);
  return fullHash.substring(0, 8);
}

/**
 * Hash multiple values together consistently
 * @param values - Array of values to hash together
 * @returns Promise resolving to hex hash string
 */
export async function hashValues(...values: (string | number | boolean)[]): Promise<string> {
  const combined = values.map(v => String(v)).join('|');
  return sha256(combined);
}

/**
 * Simple non-cryptographic hash for client-side use (synchronous)
 * Useful for quick hashing when crypto API is not needed
 * @param str - String to hash
 * @returns Hash number
 */
export function simpleHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash;
}

/**
 * Create a hash-based cache key for client logs
 * @param prefix - Key prefix
 * @param data - Data to include in hash
 * @returns Promise resolving to cache key
 */
export async function createLogCacheKey(prefix: string, data: unknown): Promise<string> {
  const dataStr = typeof data === 'string' ? data : JSON.stringify(data);
  const hash = await shortHash(dataStr);
  return `${prefix}:${hash}`;
}

/**
 * Hash sensitive data for logging (removes PII but maintains uniqueness)
 * @param text - Text that may contain sensitive data
 * @returns Promise resolving to hash suitable for logging
 */
export async function hashForLogging(text: string): Promise<string> {
  // For logging, we use short hash to avoid exposing full content
  // while still allowing correlation of related log entries
  return shortHash(text);
}

/**
 * Create deterministic session ID from user/session data
 * @param userId - User identifier (can be hashed email, etc.)
 * @param sessionData - Additional session context
 * @returns Promise resolving to session hash
 */
export async function createSessionHash(userId: string, sessionData?: string): Promise<string> {
  const combined = sessionData ? `${userId}:${sessionData}` : userId;
  return shortHash(combined);
}