// Tests for fetch streaming functionality

import { describe, it, expect, vi, beforeEach } from 'vitest';

import { parseFetchSSEMessage, parseRagStreamMessage } from '@/shared/lib/fetchStream';

describe('Fetch Streaming', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('parseFetchSSEMessage', () => {
    it('should parse simple SSE message', () => {
      const sseText = 'event: token\ndata: Hello world\n';
      const message = parseFetchSSEMessage(sseText);
      
      expect(message).toEqual({
        event: 'token',
        data: 'Hello world',
        id: undefined,
        retry: undefined,
      });
    });

    it('should parse SSE message with ID and retry', () => {
      const sseText = 'id: msg-123\nevent: token\ndata: Hello\nretry: 5000\n';
      const message = parseFetchSSEMessage(sseText);
      
      expect(message).toEqual({
        id: 'msg-123',
        event: 'token',
        data: 'Hello',
        retry: 5000,
      });
    });

    it('should handle multiline data', () => {
      const sseText = 'event: token\ndata: Line 1\ndata: Line 2\n';
      const message = parseFetchSSEMessage(sseText);
      
      expect(message).toEqual({
        event: 'token',
        data: 'Line 1\nLine 2',
        id: undefined,
        retry: undefined,
      });
    });

    it('should return null for message without data', () => {
      const sseText = 'event: heartbeat\n';
      const message = parseFetchSSEMessage(sseText);
      
      expect(message).toBeNull();
    });
  });

  describe('parseRagStreamMessage', () => {
    it('should parse JSON RAG message', () => {
      const sseMessage = {
        id: 'test-id',
        event: 'token',
        data: JSON.stringify({
          type: 'token',
          content: 'Hello from RAG',
          requestId: 'req-123',
        }),
      };
      
      const ragEvent = parseRagStreamMessage(sseMessage);
      
      expect(ragEvent).toEqual({
        type: 'token',
        content: 'Hello from RAG',
        requestId: 'req-123',
        error: undefined,
        metadata: undefined,
      });
    });

    it('should parse plain text as token', () => {
      const sseMessage = {
        id: 'test-id',
        event: 'message',
        data: 'Plain text content',
      };
      
      const ragEvent = parseRagStreamMessage(sseMessage);
      
      expect(ragEvent).toEqual({
        type: 'token',
        content: 'Plain text content',
        requestId: 'test-id',
        error: undefined,
        metadata: undefined,
      });
    });

    it('should handle error events', () => {
      const sseMessage = {
        id: 'test-id',
        event: 'error',
        data: JSON.stringify({
          type: 'error',
          error: 'Something went wrong',
          requestId: 'req-123',
        }),
      };
      
      const ragEvent = parseRagStreamMessage(sseMessage);
      
      expect(ragEvent).toEqual({
        type: 'error',
        error: 'Something went wrong',
        requestId: 'req-123',
        content: undefined,
        metadata: undefined,
      });
    });

    it('should return null for invalid JSON', () => {
      const sseMessage = {
        id: 'test-id',
        event: 'message',
        data: '{ invalid json',
      };
      
      const ragEvent = parseRagStreamMessage(sseMessage);
      
      expect(ragEvent).toBeNull();
    });
  });
});