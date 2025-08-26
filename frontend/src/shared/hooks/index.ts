// React hooks for cross-cutting concerns

import { useEffect, useState, useRef, useCallback } from 'react';
import { EventStreamManager, StreamMessage, StreamOptions, StreamEventHandlers } from '@/api/streaming';
import { logger } from '@/shared/lib/logger';

/**
 * Hook for managing Server-Sent Events streams
 */
export function useEventStream(
  url: string | null,
  options: StreamOptions = {}
) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  
  const streamRef = useRef<EventStreamManager | null>(null);
  const handlersRef = useRef<StreamEventHandlers>({});

  // Update handlers ref to avoid recreating stream manager
  handlersRef.current = {
    onOpen: () => {
      setIsConnected(true);
      setError(null);
      logger.info('Stream connected');
    },
    onClose: () => {
      setIsConnected(false);
      logger.info('Stream disconnected');
    },
    onError: (event) => {
      setError(event);
      setIsConnected(false);
      logger.error('Stream error', event);
    },
    onMessage: (message) => {
      setMessages(prev => [...prev, message]);
    },
  };

  const connect = useCallback(() => {
    if (!url || streamRef.current) {
      return;
    }

    streamRef.current = new EventStreamManager(url, handlersRef.current, options);
    streamRef.current.connect();
  }, [url, options]);

  const disconnect = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.disconnect();
      streamRef.current = null;
    }
    setIsConnected(false);
    setError(null);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Auto-connect when URL is provided
  useEffect(() => {
    if (url) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [url, connect, disconnect]);

  return {
    isConnected,
    error,
    messages,
    connect,
    disconnect,
    clearMessages,
  };
}

/**
 * Hook for debouncing values
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for managing localStorage with SSR safety
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((val: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      logger.warn('Failed to read from localStorage', { key, error });
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      logger.error('Failed to write to localStorage', { key, error });
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
}

/**
 * Hook for detecting window focus
 */
export function useWindowFocus(): boolean {
  const [focused, setFocused] = useState(() =>
    typeof window !== 'undefined' ? document.hasFocus() : true
  );

  useEffect(() => {
    const onFocus = () => setFocused(true);
    const onBlur = () => setFocused(false);

    window.addEventListener('focus', onFocus);
    window.addEventListener('blur', onBlur);

    return () => {
      window.removeEventListener('focus', onFocus);
      window.removeEventListener('blur', onBlur);
    };
  }, []);

  return focused;
}