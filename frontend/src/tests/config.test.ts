import { describe, it, expect } from 'vitest';

import { getConfig } from '@/shared/config';

describe('Configuration', () => {
  it('should load configuration with defaults', () => {
    const config = getConfig();
    
    expect(config).toBeDefined();
    expect(config.PUBLIC_API_BASE_URL).toBe('http://localhost:8000/api');
    expect(config.FEATURE_RAG).toBe(true); // Set in setupTests
    expect(config.FEATURE_ANALYTICS_UPLOAD).toBe(false);
    expect(config.DEFAULT_LOCALE).toBe('en');
  });

  it('should validate configuration schema', () => {
    const config = getConfig();
    
    // Should be a valid URL
    expect(() => new URL(config.PUBLIC_API_BASE_URL)).not.toThrow();
    
    // Should be valid locale
    expect(['en', 'nl']).toContain(config.DEFAULT_LOCALE);
    
    // Should be boolean values
    expect(typeof config.FEATURE_RAG).toBe('boolean');
    expect(typeof config.FEATURE_ANALYTICS_UPLOAD).toBe('boolean');
  });
});