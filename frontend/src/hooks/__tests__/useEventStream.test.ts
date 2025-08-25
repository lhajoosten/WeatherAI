// Tests for useEventStream hook

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useEventStream } from '@/hooks';

// Mock EventSource
const mockEventSource = {
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  close: vi.fn(),
  readyState: 1,
  onopen: null as ((event: Event) => void) | null,
  onmessage: null as ((event: MessageEvent) => void) | null,
  onerror: null as ((event: Event) => void) | null,
};

const mockEventSourceConstructor = vi.fn(() => mockEventSource);

// Mock global EventSource
Object.defineProperty(globalThis, 'EventSource', {
  value: mockEventSourceConstructor,
  writable: true,
});

describe('useEventStream', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should not connect when url is null', () => {
    const { result } = renderHook(() => useEventStream(null));

    expect(result.current.isConnected).toBe(false);
    expect(mockEventSourceConstructor).not.toHaveBeenCalled();
  });

  it('should connect when url is provided', () => {
    const url = 'http://localhost:3000/stream';
    renderHook(() => useEventStream(url));

    expect(mockEventSourceConstructor).toHaveBeenCalledWith(url);
  });

  it('should update connection state on open', async () => {
    const url = 'http://localhost:3000/stream';
    const { result } = renderHook(() => useEventStream(url));

    // Simulate connection open
    const openEvent = new Event('open');
    if (mockEventSource.onopen) {
      mockEventSource.onopen(openEvent);
    }

    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });
  });

  it('should handle messages', async () => {
    const url = 'http://localhost:3000/stream';
    const { result } = renderHook(() => useEventStream(url));

    // Simulate message
    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify({ test: 'data' }),
      lastEventId: 'test-id',
    });

    if (mockEventSource.onmessage) {
      mockEventSource.onmessage(messageEvent);
    }

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toMatchObject({
        id: 'test-id',
        data: { test: 'data' },
      });
    });
  });

  it('should handle errors', async () => {
    const url = 'http://localhost:3000/stream';
    const { result } = renderHook(() => useEventStream(url));

    // Simulate error
    const errorEvent = new Event('error');
    if (mockEventSource.onerror) {
      mockEventSource.onerror(errorEvent);
    }

    await waitFor(() => {
      expect(result.current.error).toBe(errorEvent);
      expect(result.current.isConnected).toBe(false);
    });
  });

  it('should disconnect and cleanup on unmount', () => {
    const url = 'http://localhost:3000/stream';
    const { unmount } = renderHook(() => useEventStream(url));

    unmount();

    expect(mockEventSource.close).toHaveBeenCalled();
  });

  it('should clear messages when clearMessages is called', async () => {
    const url = 'http://localhost:3000/stream';
    const { result } = renderHook(() => useEventStream(url));

    // Add a message first
    const messageEvent = new MessageEvent('message', {
      data: 'test',
      lastEventId: 'test-id',
    });

    if (mockEventSource.onmessage) {
      mockEventSource.onmessage(messageEvent);
    }

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });

    // Clear messages
    result.current.clearMessages();

    expect(result.current.messages).toHaveLength(0);
  });
});