import { describe, it, expect } from 'vitest';

import { mapToAppError } from '@/shared/api/errors';

describe('Error Mapping', () => {
  it('should map network errors correctly', () => {
    const networkError = { message: 'Network Error' };
    const appError = mapToAppError(networkError);
    
    expect(appError.kind).toBe('network');
    expect(appError.message).toBe('Network error. Please check your connection.');
  });

  it('should map timeout errors correctly', () => {
    const timeoutError = { code: 'ECONNABORTED', message: 'timeout of 5000ms exceeded' };
    const appError = mapToAppError(timeoutError);
    
    expect(appError.kind).toBe('timeout');
    expect(appError.message).toBe('Request timed out. Please try again.');
  });

  it('should map client errors (4xx) correctly', () => {
    const clientError = {
      response: {
        status: 400,
        data: { message: 'Bad Request' }
      }
    };
    const appError = mapToAppError(clientError);
    
    expect(appError.kind).toBe('client');
    expect(appError.message).toBe('Bad Request');
    expect(appError.status).toBe(400);
  });

  it('should map server errors (5xx) correctly', () => {
    const serverError = {
      response: {
        status: 500,
        data: { message: 'Internal Server Error' }
      }
    };
    const appError = mapToAppError(serverError);
    
    expect(appError.kind).toBe('server');
    expect(appError.message).toBe('Server error. Please try again later.');
    expect(appError.status).toBe(500);
  });

  it('should map unknown status codes correctly', () => {
    const unknownError = {
      response: {
        status: 300, // 3xx status - not handled specifically, should be unknown
        data: { message: "Redirection status" }
      }
    };
    const appError = mapToAppError(unknownError);
    
    expect(appError.kind).toBe('unknown');
    expect(appError.status).toBe(300);
  });
});