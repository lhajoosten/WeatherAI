// Enhanced app error types aligned with backend Problem+JSON format

export type AppErrorKind = 
  | 'network'
  | 'client' 
  | 'server'
  | 'timeout'
  | 'validation'
  | 'authentication'
  | 'authorization'
  | 'not_found'
  | 'conflict'
  | 'unknown';

/**
 * Application error type aligned with RFC 7807 Problem Details
 */
export interface AppError {
  kind: AppErrorKind;
  message: string;
  title?: string;
  type?: string;
  status?: number;
  detail?: string;
  instance?: string;
  traceId?: string;
  code?: string;
  timestamp?: string;
  extensions?: Record<string, unknown>;
}

/**
 * Factory functions for creating AppError instances
 */
export const createAppError = {
  network: (message: string, details?: Partial<AppError>): AppError => ({
    kind: 'network',
    message,
    type: 'about:blank',
    ...details,
  }),
  
  client: (message: string, status: number, details?: Partial<AppError>): AppError => ({
    kind: 'client',
    message,
    status,
    type: 'about:blank',
    ...details,
  }),
  
  server: (message: string, status: number, details?: Partial<AppError>): AppError => ({
    kind: 'server',
    message,
    status,
    type: 'about:blank',
    ...details,
  }),
  
  timeout: (message: string = 'Request timeout'): AppError => ({
    kind: 'timeout',
    message,
    type: 'about:blank',
  }),
  
  validation: (message: string, details?: Partial<AppError>): AppError => ({
    kind: 'validation',
    message,
    status: 400,
    type: 'about:blank',
    ...details,
  }),
  
  unknown: (message: string = 'An unknown error occurred'): AppError => ({
    kind: 'unknown',
    message,
    type: 'about:blank',
  }),
};

/**
 * Type guards for AppError kinds
 */
export const isNetworkError = (error: AppError): boolean => error.kind === 'network';
export const isClientError = (error: AppError): boolean => error.kind === 'client';
export const isServerError = (error: AppError): boolean => error.kind === 'server';
export const isValidationError = (error: AppError): boolean => error.kind === 'validation';
export const isTimeoutError = (error: AppError): boolean => error.kind === 'timeout';

/**
 * Get user-friendly error message
 */
export function getErrorMessage(error: AppError): string {
  switch (error.kind) {
    case 'network':
      return 'Network connection failed. Please check your internet connection.';
    case 'timeout':
      return 'Request timed out. Please try again.';
    case 'authentication':
      return 'Please log in to continue.';
    case 'authorization':
      return 'You do not have permission to perform this action.';
    case 'not_found':
      return 'The requested resource was not found.';
    case 'validation':
      return error.detail || error.message || 'Invalid input data.';
    case 'server':
      return 'A server error occurred. Please try again later.';
    default:
      return error.message || 'An unexpected error occurred.';
  }
}

/**
 * Check if error should trigger a retry
 */
export function shouldRetry(error: AppError): boolean {
  return error.kind === 'network' || error.kind === 'timeout' || 
         (error.kind === 'server' && error.status !== 500);
}