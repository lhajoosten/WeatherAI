import { z } from 'zod';

// Environment config schema
const envConfigSchema = z.object({
  apiUrl: z.string().url().default('http://localhost:8000/api'),
  environment: z.enum(['development', 'staging', 'production']).default('development'),
  enableDevTools: z.boolean().default(true),
  logLevel: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
});

export type EnvConfig = z.infer<typeof envConfigSchema>;

// Load and validate environment configuration
function loadEnvConfig(): EnvConfig {
  const rawConfig = {
    apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
    environment: import.meta.env.VITE_ENV || 'development',
    enableDevTools: import.meta.env.VITE_ENABLE_DEV_TOOLS !== 'false',
    logLevel: import.meta.env.VITE_LOG_LEVEL || 'info',
  };

  try {
    return envConfigSchema.parse(rawConfig);
  } catch (error) {
    console.error('Invalid environment configuration:', error);
    // Return defaults if validation fails
    return envConfigSchema.parse({});
  }
}

// Singleton config instance
let configInstance: EnvConfig | null = null;

export function getConfig(): EnvConfig {
  if (!configInstance) {
    configInstance = loadEnvConfig();
  }
  return configInstance;
}

export default getConfig;