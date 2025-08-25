/**
 * Development logger - logs to console
 * Future: could send to backend analytics endpoint
 */
export const logger = {
  debug: (message: string, data?: any) => {
    console.debug(`[DEBUG] ${message}`, data);
  },
  info: (message: string, data?: any) => {
    console.info(`[INFO] ${message}`, data);
  },
  warn: (message: string, data?: any) => {
    console.warn(`[WARN] ${message}`, data);
  },
  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error);
  },
};

/**
 * Records metrics for future analytics
 * Currently logs to console, future: send to backend
 */
export const recordMetric = (name: string, value: number, tags?: Record<string, string>) => {
  logger.debug('Metric recorded', { name, value, tags });
  // Future: send to analytics endpoint when FEATURE_ANALYTICS_UPLOAD is enabled
};

/**
 * Wraps a function with timing metrics using Performance API
 */
export const withTiming = async <T>(name: string, fn: () => Promise<T>): Promise<T> => {
  const start = performance.now();
  performance.mark(`${name}-start`);
  
  try {
    const result = await fn();
    const end = performance.now();
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);
    
    const duration = end - start;
    recordMetric(`${name}.duration`, duration);
    
    return result;
  } catch (error) {
    const end = performance.now();
    const duration = end - start;
    recordMetric(`${name}.error`, duration);
    throw error;
  }
};

/**
 * React hook for tracing component lifecycle with Performance API
 */
export const useTrace = (componentName: string) => {
  const markName = `${componentName}-render`;
  
  // Mark start of render
  performance.mark(`${markName}-start`);
  
  return {
    /**
     * Mark end of render and measure duration
     */
    markComplete: () => {
      performance.mark(`${markName}-end`);
      performance.measure(markName, `${markName}-start`, `${markName}-end`);
    },
  };
};