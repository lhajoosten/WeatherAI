// RAG hooks with streaming support

import { useMutation } from '@tanstack/react-query';
import { useState, useCallback } from 'react';


import { apiClient } from '@/shared/api/apiClient';
import { RagAskRequest } from '@/shared/types/api';
import { useFeatureFlags } from '@/shared/config/flags';
import { logger } from '@/shared/lib/logger';
import { delay } from '@/shared/lib/utils';

export interface RagStreamMessage {
  type: 'start' | 'token' | 'end' | 'error';
  content?: string;
  error?: string;
  requestId?: string;
}

export interface RagAskOptions {
  streaming?: boolean;
  locationId?: string;
}

/**
 * Hook for asking RAG questions with optional streaming
 */
export function useRagAsk() {
  const flags = useFeatureFlags();
  const [streamingAnswer, setStreamingAnswer] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  // Mock streaming implementation until backend is ready
  const startMockStream = useCallback(async (query: string) => {
    if (!flags.rag.enabled) {
      throw new Error('RAG feature is not enabled');
    }

    setIsStreaming(true);
    setStreamingAnswer('');
    
    // Simulate streaming response with mock data
    const mockResponse = `Based on the weather data for your query "${query}", here are the key insights:

1. Current conditions show favorable weather patterns
2. Temperature trends indicate stable conditions  
3. Precipitation levels are within normal ranges
4. Wind patterns suggest mild weather ahead

This analysis is generated from multiple weather data sources and historical patterns.`;

    const words = mockResponse.split(' ');
    
    try {
      for (let i = 0; i < words.length; i++) {
        await delay(50 + Math.random() * 100); // Variable delay to simulate real streaming
        
        const partialAnswer = words.slice(0, i + 1).join(' ');
        setStreamingAnswer(partialAnswer);
      }
      
      // Simulate final processing delay
      await delay(500);
      
    } catch (error) {
      logger.error('Mock streaming error', error);
      throw error;
    } finally {
      setIsStreaming(false);
    }
  }, [flags.rag.enabled]);

  // Standard non-streaming mutation
  const askMutation = useMutation({
    mutationFn: (request: RagAskRequest) => {
      if (!flags.rag.enabled) {
        throw new Error('RAG feature is not enabled');
      }
      return apiClient.askRag(request);
    },
    onError: (error) => {
      logger.error('RAG ask failed', error);
    },
  });

  const ask = useCallback(async (query: string, options: RagAskOptions = {}) => {
    if (options.streaming) {
      return startMockStream(query);
    } else {
      return askMutation.mutateAsync({
        query,
        locationId: options.locationId,
      });
    }
  }, [askMutation, startMockStream]);

  return {
    ask,
    isLoading: askMutation.isPending || isStreaming,
    error: askMutation.error,
    data: askMutation.data,
    streamingAnswer,
    isStreaming,
    clearStreaming: () => setStreamingAnswer(''),
    isEnabled: flags.rag.enabled,
  };
}