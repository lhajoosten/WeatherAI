import { describe, it, expect, vi, beforeEach } from 'vitest';

import { recordMetric, logger, withTiming } from '@/shared/observability';

describe('Observability', () => {
  beforeEach(() => {
    // Spy on console methods
    vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.spyOn(console, 'info').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('should record metrics with console logging', () => {
    recordMetric('test.metric', 123, { tag: 'value' });
    
    expect(console.debug).toHaveBeenCalledWith(
      '[DEBUG] Metric recorded',
      { name: 'test.metric', value: 123, tags: { tag: 'value' } }
    );
  });

  it('should log messages correctly', () => {
    logger.debug('Debug message', { data: 'test' });
    logger.info('Info message');
    logger.warn('Warning message');
    logger.error('Error message', new Error('test'));

    expect(console.debug).toHaveBeenCalledWith('[DEBUG] Debug message', { data: 'test' });
    expect(console.info).toHaveBeenCalledWith('[INFO] Info message', undefined);
    expect(console.warn).toHaveBeenCalledWith('[WARN] Warning message', undefined);
    expect(console.error).toHaveBeenCalledWith('[ERROR] Error message', expect.any(Error));
  });

  it('should measure timing with withTiming', async () => {
    const testFunction = vi.fn().mockResolvedValue('result');
    const result = await withTiming('test.operation', testFunction);

    expect(result).toBe('result');
    expect(testFunction).toHaveBeenCalled();
    expect(console.debug).toHaveBeenCalledWith(
      '[DEBUG] Metric recorded',
      expect.objectContaining({
        name: 'test.operation.duration',
        value: expect.any(Number),
      })
    );
  });

  it('should handle errors in withTiming', async () => {
    const testFunction = vi.fn().mockRejectedValue(new Error('test error'));
    
    await expect(withTiming('test.operation', testFunction)).rejects.toThrow('test error');
    
    expect(console.debug).toHaveBeenCalledWith(
      '[DEBUG] Metric recorded',
      expect.objectContaining({
        name: 'test.operation.error',
        value: expect.any(Number),
      })
    );
  });
});