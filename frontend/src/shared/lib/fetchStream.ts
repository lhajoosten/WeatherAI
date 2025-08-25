// Fetch-based streaming utility for text/event-stream parsing

import { logger } from '@/shared/lib/logger';
import { generateId } from '@/shared/lib/utils';

export interface FetchStreamMessage {
  id?: string;
  event?: string;
  data: string;
  retry?: number;
}

export interface FetchStreamOptions {
  headers?: Record<string, string>;
  body?: string | FormData | URLSearchParams;
  abortController?: AbortController;
  onMessage?: (message: FetchStreamMessage) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export interface StreamResponse {
  abort: () => void;
  isComplete: boolean;
}

/**
 * Parse a single SSE message from text
 */
export function parseFetchSSEMessage(text: string): FetchStreamMessage | null {
  const lines = text.trim().split('\n');
  const message: Partial<FetchStreamMessage> = {};
  
  for (const line of lines) {
    if (line === '') continue;
    
    const colonIndex = line.indexOf(':');
    if (colonIndex === -1) continue;
    
    const field = line.slice(0, colonIndex).trim();
    const value = line.slice(colonIndex + 1).trim();
    
    switch (field) {
      case 'id':
        message.id = value;
        break;
      case 'event':
        message.event = value;
        break;
      case 'data':
        message.data = (message.data || '') + value + '\n';
        break;
      case 'retry':
        message.retry = parseInt(value, 10);
        break;
    }
  }
  
  if (message.data !== undefined) {
    // Remove trailing newline from data
    message.data = message.data.replace(/\n$/, '');
    return {
      id: message.id,
      event: message.event,
      data: message.data,
      retry: message.retry,
    };
  }
  
  return null;
}

/**
 * Stream data from a fetch ReadableStream for text/event-stream responses
 */
export async function createFetchStream(
  url: string,
  options: FetchStreamOptions = {}
): Promise<StreamResponse> {
  const abortController = options.abortController || new AbortController();
  let isComplete = false;
  
  const streamResponse: StreamResponse = {
    abort: () => {
      if (!isComplete) {
        abortController.abort();
      }
    },
    isComplete: false,
  };
  
  try {
    logger.info('Starting fetch stream', { url });
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: options.body,
      signal: abortController.signal,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
    }
    
    if (!response.body) {
      throw new Error('No response body available');
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          logger.info('Fetch stream completed');
          break;
        }
        
        // Decode chunk and add to buffer
        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        // Process complete messages (delimited by double newlines)
        const messages = buffer.split('\n\n');
        buffer = messages.pop() || ''; // Keep incomplete message in buffer
        
        for (const messageText of messages) {
          if (messageText.trim()) {
            const message = parseFetchSSEMessage(messageText);
            if (message) {
              logger.debug('Received stream message', { 
                event: message.event, 
                dataLength: message.data.length 
              });
              options.onMessage?.(message);
            }
          }
        }
      }
      
      // Process any remaining data in buffer
      if (buffer.trim()) {
        const message = parseFetchSSEMessage(buffer);
        if (message) {
          options.onMessage?.(message);
        }
      }
      
    } finally {
      reader.releaseLock();
    }
    
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      logger.info('Fetch stream aborted');
    } else {
      logger.error('Fetch stream error', error);
      options.onError?.(error instanceof Error ? error : new Error(String(error)));
    }
  } finally {
    isComplete = true;
    streamResponse.isComplete = true;
    options.onComplete?.();
  }
  
  return streamResponse;
}

/**
 * Utility function for common RAG streaming events
 */
export interface RagStreamEvent {
  type: 'start' | 'token' | 'done' | 'error';
  content?: string;
  error?: string;
  requestId?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Parse RAG-specific stream messages
 */
export function parseRagStreamMessage(message: FetchStreamMessage): RagStreamEvent | null {
  try {
    // Handle JSON data
    if (message.data.startsWith('{')) {
      const parsed = JSON.parse(message.data);
      return {
        type: parsed.type || 'token',
        content: parsed.content,
        error: parsed.error,
        requestId: parsed.requestId || message.id,
        metadata: parsed.metadata,
      };
    }
    
    // Handle plain text as token
    return {
      type: 'token',
      content: message.data,
      requestId: message.id || generateId(),
    };
  } catch (error) {
    logger.warn('Failed to parse RAG stream message', { message, error });
    return null;
  }
}

/**
 * Create a RAG stream with typed events
 */
export async function createRagStream(
  url: string,
  body: unknown,
  options: {
    onStart?: () => void;
    onToken?: (content: string, requestId?: string) => void;
    onDone?: (requestId?: string) => void;
    onError?: (error: string, requestId?: string) => void;
    abortController?: AbortController;
  } = {}
): Promise<StreamResponse> {
  return createFetchStream(url, {
    body: JSON.stringify(body),
    abortController: options.abortController,
    onMessage: (message) => {
      const ragEvent = parseRagStreamMessage(message);
      if (!ragEvent) return;
      
      switch (ragEvent.type) {
        case 'start':
          options.onStart?.();
          break;
        case 'token':
          if (ragEvent.content) {
            options.onToken?.(ragEvent.content, ragEvent.requestId);
          }
          break;
        case 'done':
          options.onDone?.(ragEvent.requestId);
          break;
        case 'error':
          if (ragEvent.error) {
            options.onError?.(ragEvent.error, ragEvent.requestId);
          }
          break;
      }
    },
    onError: (error) => {
      options.onError?.(error.message);
    },
  });
}