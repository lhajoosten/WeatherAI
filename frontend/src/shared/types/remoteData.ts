/**
 * RemoteData represents the state of an asynchronous operation.
 * This pattern helps manage loading states and errors in a type-safe way.
 */

export type RemoteData<T, E = AppError> =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'success'; data: T }
  | { kind: 'error'; error: E };

/**
 * App-wide error types with discriminated union for type safety
 */
export type AppErrorKind = 'network' | 'client' | 'server' | 'timeout' | 'unknown';

export interface AppError {
  kind: AppErrorKind;
  message: string;
  status?: number;
  details?: Record<string, any>;
}

/**
 * Type guards for RemoteData states
 */
export const isIdle = <T, E>(data: RemoteData<T, E>): data is { kind: 'idle' } => 
  data.kind === 'idle';

export const isLoading = <T, E>(data: RemoteData<T, E>): data is { kind: 'loading' } => 
  data.kind === 'loading';

export const isSuccess = <T, E>(data: RemoteData<T, E>): data is { kind: 'success'; data: T } => 
  data.kind === 'success';

export const isError = <T, E>(data: RemoteData<T, E>): data is { kind: 'error'; error: E } => 
  data.kind === 'error';

/**
 * Helper function for exhaustive checking in switch statements
 */
export const assertNever = (value: never): never => {
  throw new Error(`Unexpected value: ${value}`);
};

/**
 * Factory functions for creating RemoteData instances
 */
export const remoteData = {
  idle: <T, E = AppError>(): RemoteData<T, E> => ({ kind: 'idle' }),
  loading: <T, E = AppError>(): RemoteData<T, E> => ({ kind: 'loading' }),
  success: <T, E = AppError>(data: T): RemoteData<T, E> => ({ kind: 'success', data }),
  error: <T, E = AppError>(error: E): RemoteData<T, E> => ({ kind: 'error', error }),
};