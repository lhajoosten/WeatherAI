import { z } from 'zod';

// Runtime config schema for env-injected values
const appConfigSchema = z.object({
  PUBLIC_API_BASE_URL: z.string().url().default('http://localhost:8000/api'),
  FEATURE_RAG: z.boolean().default(false),
  FEATURE_ANALYTICS_UPLOAD: z.boolean().default(false),
  DEFAULT_LOCALE: z.enum(['en', 'nl']).default('en'),
});

export type AppConfig = z.infer<typeof appConfigSchema>;

/**
 * Loads configuration from window.__APP_CONFIG__ (injected at runtime)
 * Falls back to process.env.* for build-time configuration
 */
export function loadConfig(): AppConfig {
  // Check for runtime config injected by server
  const runtimeConfig = (window as any).__APP_CONFIG__;
  
  if (runtimeConfig) {
    try {
      return appConfigSchema.parse(runtimeConfig);
    } catch (error) {
      console.error('Invalid runtime config:', error);
      // Fall through to build-time config
    }
  }

  // Fall back to build-time environment variables
  const buildConfig = {
    PUBLIC_API_BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
    FEATURE_RAG: import.meta.env.VITE_FEATURE_RAG === 'true',
    FEATURE_ANALYTICS_UPLOAD: import.meta.env.VITE_FEATURE_ANALYTICS_UPLOAD === 'true',
    DEFAULT_LOCALE: import.meta.env.VITE_DEFAULT_LOCALE || 'en',
  };

  try {
    return appConfigSchema.parse(buildConfig);
  } catch (error) {
    console.error('Invalid build config, using defaults:', error);
    return appConfigSchema.parse({});
  }
}

// Singleton config instance
let configInstance: AppConfig | null = null;

export function getConfig(): AppConfig {
  if (!configInstance) {
    configInstance = loadConfig();
  }
  return configInstance;
}