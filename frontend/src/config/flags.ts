// Feature flags configuration

export interface FeatureFlags {
  rag: {
    enabled: boolean;
  };
  analytics: {
    upload: boolean;
  };
  streaming: {
    enabled: boolean;
  };
}

/**
 * Get feature flags from environment variables
 */
export function getFeatureFlags(): FeatureFlags {
  return {
    rag: {
      enabled: import.meta.env.VITE_FEATURE_RAG === '1' || import.meta.env.VITE_FEATURE_RAG === 'true',
    },
    analytics: {
      upload: import.meta.env.VITE_FEATURE_ANALYTICS_UPLOAD === '1' || import.meta.env.VITE_FEATURE_ANALYTICS_UPLOAD === 'true',
    },
    streaming: {
      enabled: import.meta.env.VITE_FEATURE_STREAMING === '1' || import.meta.env.VITE_FEATURE_STREAMING === 'true',
    },
  };
}

// Singleton instance
let flagsInstance: FeatureFlags | null = null;

export function useFeatureFlags(): FeatureFlags {
  if (!flagsInstance) {
    flagsInstance = getFeatureFlags();
  }
  return flagsInstance;
}