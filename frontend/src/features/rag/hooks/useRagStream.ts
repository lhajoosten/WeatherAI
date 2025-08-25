// RAG Stream hook using fetch streaming

import { useState, useCallback, useRef } from 'react';

import { useFeatureFlags } from '@/config/flags';
import { createRagStream, StreamResponse } from '@/shared/lib/fetchStream';
import { logger } from '@/shared/lib/logger';

export interface RagStreamState {
  isStreaming: boolean;
  content: string;
  error: string | null;
  requestId: string | null;
  isComplete: boolean;
}

export interface RagStreamRequest {
  query: string;
  locationId?: string;
  context?: string;
}

export interface UseRagStreamOptions {
  endpoint?: string;
  onComplete?: (content: string) => void;
  onError?: (error: string) => void;
}

export function useRagStream(options: UseRagStreamOptions = {}) {
  const flags = useFeatureFlags();
  const streamRef = useRef<StreamResponse | null>(null);
  
  const [state, setState] = useState<RagStreamState>({
    isStreaming: false,
    content: '',
    error: null,
    requestId: null,
    isComplete: false,
  });

  const startStream = useCallback(async (request: RagStreamRequest) => {
    if (!flags.rag.enabled) {
      const error = 'RAG feature is not enabled';
      setState(prev => ({ ...prev, error }));
      throw new Error(error);
    }

    if (!flags.streaming.enabled) {
      const error = 'Streaming feature is not enabled';
      setState(prev => ({ ...prev, error }));
      throw new Error(error);
    }

    // Reset state
    setState({
      isStreaming: true,
      content: '',
      error: null,
      requestId: null,
      isComplete: false,
    });

    try {
      const endpoint = options.endpoint || '/api/rag/stream';
      logger.info('Starting RAG stream', { query: request.query, endpoint });

      const stream = await createRagStream(endpoint, request, {
        onStart: () => {
          logger.debug('RAG stream started');
        },
        onToken: (content, requestId) => {
          setState(prev => ({
            ...prev,
            content: prev.content + content,
            requestId: requestId || prev.requestId,
          }));
        },
        onDone: (requestId) => {
          logger.info('RAG stream completed', { requestId });
          setState(prev => ({
            ...prev,
            isStreaming: false,
            isComplete: true,
            requestId: requestId || prev.requestId,
          }));
          options.onComplete?.(state.content);
        },
        onError: (error, requestId) => {
          logger.error('RAG stream error', { error, requestId });
          setState(prev => ({
            ...prev,
            isStreaming: false,
            error,
            requestId: requestId || prev.requestId,
          }));
          options.onError?.(error);
        },
      });

      streamRef.current = stream;
      return stream;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      logger.error('Failed to start RAG stream', error);
      
      setState(prev => ({
        ...prev,
        isStreaming: false,
        error: errorMessage,
      }));
      
      options.onError?.(errorMessage);
      throw error;
    }
  }, [flags, options, state.content]);

  const stopStream = useCallback(() => {
    if (streamRef.current && !streamRef.current.isComplete) {
      logger.info('Stopping RAG stream');
      streamRef.current.abort();
      setState(prev => ({
        ...prev,
        isStreaming: false,
      }));
    }
  }, []);

  const clearContent = useCallback(() => {
    setState(prev => ({
      ...prev,
      content: '',
      error: null,
      isComplete: false,
      requestId: null,
    }));
  }, []);

  const reset = useCallback(() => {
    stopStream();
    clearContent();
  }, [stopStream, clearContent]);

  return {
    // State
    isStreaming: state.isStreaming,
    content: state.content,
    error: state.error,
    requestId: state.requestId,
    isComplete: state.isComplete,
    
    // Actions
    startStream,
    stopStream,
    clearContent,
    reset,
    
    // Computed
    hasContent: state.content.length > 0,
    hasError: state.error !== null,
    isEnabled: flags.rag.enabled && flags.streaming.enabled,
  };
}