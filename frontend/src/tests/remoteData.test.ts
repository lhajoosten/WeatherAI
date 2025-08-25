import { describe, it, expect } from 'vitest';

import { remoteData, isIdle, isLoading, isSuccess, isError } from '@/shared/types';

describe('RemoteData', () => {
  it('should create idle state correctly', () => {
    const idle = remoteData.idle();
    expect(idle.kind).toBe('idle');
    expect(isIdle(idle)).toBe(true);
    expect(isLoading(idle)).toBe(false);
    expect(isSuccess(idle)).toBe(false);
    expect(isError(idle)).toBe(false);
  });

  it('should create loading state correctly', () => {
    const loading = remoteData.loading();
    expect(loading.kind).toBe('loading');
    expect(isLoading(loading)).toBe(true);
    expect(isIdle(loading)).toBe(false);
    expect(isSuccess(loading)).toBe(false);
    expect(isError(loading)).toBe(false);
  });

  it('should create success state correctly', () => {
    const data = { test: 'value' };
    const success = remoteData.success(data);
    expect(success.kind).toBe('success');
    expect(isSuccess(success)).toBe(true);
    if (isSuccess(success)) {
      expect(success.data).toEqual(data);
    }
    expect(isIdle(success)).toBe(false);
    expect(isLoading(success)).toBe(false);
    expect(isError(success)).toBe(false);
  });

  it('should create error state correctly', () => {
    const error = { kind: 'network' as const, message: 'Network error' };
    const errorState = remoteData.error(error);
    expect(errorState.kind).toBe('error');
    expect(isError(errorState)).toBe(true);
    if (isError(errorState)) {
      expect(errorState.error).toEqual(error);
    }
    expect(isIdle(errorState)).toBe(false);
    expect(isLoading(errorState)).toBe(false);
    expect(isSuccess(errorState)).toBe(false);
  });
});