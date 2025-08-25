// Server-Sent Events streaming infrastructure

import { logger } from '@/shared/lib/logger';
import { generateId } from '@/shared/lib/utils';

export interface StreamMessage {
  id: string;
  event?: string;
  data: unknown;
  retry?: number;
}

export interface StreamOptions {
  retryInterval?: number;
  maxRetries?: number;
  reconnectOnError?: boolean;
}

export interface StreamEventHandlers {
  onMessage?: (message: StreamMessage) => void;
  onError?: (error: Event) => void;
  onOpen?: (event: Event) => void;
  onClose?: () => void;
}

/**
 * Generic Server-Sent Events stream manager
 */
export class EventStreamManager {
  private eventSource: EventSource | null = null;
  private url: string;
  private options: StreamOptions;
  private handlers: StreamEventHandlers;
  private retryCount = 0;
  private isConnected = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    url: string,
    handlers: StreamEventHandlers,
    options: StreamOptions = {}
  ) {
    this.url = url;
    this.handlers = handlers;
    this.options = {
      retryInterval: 5000,
      maxRetries: 5,
      reconnectOnError: true,
      ...options,
    };
  }

  /**
   * Start the event stream connection
   */
  connect(): void {
    if (this.eventSource) {
      logger.warn('Stream already connected');
      return;
    }

    logger.info('Connecting to event stream', { url: this.url });

    this.eventSource = new EventSource(this.url);

    this.eventSource.onopen = (event) => {
      logger.info('Stream connected');
      this.isConnected = true;
      this.retryCount = 0;
      this.handlers.onOpen?.(event);
    };

    this.eventSource.onmessage = (event) => {
      try {
        const message: StreamMessage = {
          id: event.lastEventId || generateId(),
          event: event.type,
          data: this.parseEventData(event.data),
        };
        
        this.handlers.onMessage?.(message);
      } catch (error) {
        logger.error('Failed to parse stream message', error);
      }
    };

    this.eventSource.onerror = (event) => {
      logger.error('Stream error', event);
      this.isConnected = false;
      this.handlers.onError?.(event);
      
      if (this.options.reconnectOnError && this.retryCount < (this.options.maxRetries || 5)) {
        this.scheduleReconnect();
      }
    };
  }

  /**
   * Close the event stream connection
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.eventSource) {
      logger.info('Disconnecting from event stream');
      this.eventSource.close();
      this.eventSource = null;
      this.isConnected = false;
      this.handlers.onClose?.();
    }
  }

  /**
   * Check if the stream is currently connected
   */
  get connected(): boolean {
    return this.isConnected;
  }

  private parseEventData(data: string): unknown {
    if (!data || data.trim() === '') {
      return null;
    }

    // Handle heartbeat/keep-alive comments
    if (data.startsWith(':')) {
      return { type: 'heartbeat', message: data.slice(1).trim() };
    }

    try {
      return JSON.parse(data);
    } catch {
      // Return as plain text if not JSON
      return data;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return;
    }

    this.retryCount++;
    const delay = this.options.retryInterval! * Math.pow(2, this.retryCount - 1); // Exponential backoff

    logger.info(`Scheduling reconnect in ${delay}ms (attempt ${this.retryCount})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.disconnect();
      this.connect();
    }, delay);
  }
}

/**
 * Parse Server-Sent Events formatted text
 */
export function parseSSEMessage(rawMessage: string): StreamMessage[] {
  const messages: StreamMessage[] = [];
  const lines = rawMessage.split('\n');
  let currentMessage: Partial<StreamMessage> = {};

  for (const line of lines) {
    if (line === '') {
      // Empty line indicates end of message
      if (currentMessage.data !== undefined) {
        messages.push({
          id: currentMessage.id || generateId(),
          event: currentMessage.event,
          data: currentMessage.data,
          retry: currentMessage.retry,
        });
      }
      currentMessage = {};
      continue;
    }

    const colonIndex = line.indexOf(':');
    if (colonIndex === -1) {
      continue;
    }

    const field = line.slice(0, colonIndex);
    const value = line.slice(colonIndex + 1).trim();

    switch (field) {
      case 'id':
        currentMessage.id = value;
        break;
      case 'event':
        currentMessage.event = value;
        break;
      case 'data':
        currentMessage.data = value;
        break;
      case 'retry':
        currentMessage.retry = parseInt(value, 10);
        break;
    }
  }

  return messages;
}