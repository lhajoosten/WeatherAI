import { AppError, AppErrorKind } from '@/shared/types';

/**
 * Maps HTTP status codes and error types to AppError instances
 */
export const mapToAppError = (error: any): AppError => {
  // Network errors (no response)
  if (!error.response) {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      return {
        kind: 'timeout',
        message: 'Request timed out. Please try again.',
        details: { originalError: error.message },
      };
    }
    return {
      kind: 'network',
      message: 'Network error. Please check your connection.',
      details: { originalError: error.message },
    };
  }

  const status = error.response.status;
  const data = error.response.data;
  const message = data?.message || data?.detail || error.message || 'An error occurred';

  // Client errors (4xx)
  if (status >= 400 && status < 500) {
    return {
      kind: 'client',
      message,
      status,
      details: data,
    };
  }

  // Server errors (5xx)
  if (status >= 500) {
    return {
      kind: 'server',
      message: 'Server error. Please try again later.',
      status,
      details: data,
    };
  }

  // Unknown errors
  return {
    kind: 'unknown',
    message,
    status,
    details: data,
  };
};

/**
 * Creates an AppError from a generic error
 */
export const createAppError = (
  kind: AppErrorKind,
  message: string,
  status?: number,
  details?: Record<string, any>
): AppError => ({
  kind,
  message,
  status,
  details,
});