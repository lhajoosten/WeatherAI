import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Textarea,
  Button,
  Text,
  Alert,
  AlertIcon,
  Spinner,
  useColorModeValue,
  FormControl,
  FormLabel,
  Switch,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Badge,
} from '@chakra-ui/react';
import { Send, Settings } from 'react-feather';
import { useRagAsk } from '../hooks/useRagAsk';
import RagSourceCard from './RagSourceCard';
import type { QueryResponse } from '@/shared/types/api';

const RagQueryInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [maxSources, setMaxSources] = useState(5);
  const [minSimilarity, setMinSimilarity] = useState(0.7);
  const [streaming, setStreaming] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);

  const { ask, isLoading, error, reset } = useRagAsk();

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  const handleSubmit = async () => {
    if (!query.trim()) return;

    try {
      reset();
      const response = await ask(query, {
        streaming,
        maxSources,
        minSimilarity,
      });
      
      if (response && 'answer' in response) {
        setResult(response as QueryResponse);
      }
    } catch (err) {
      console.error('Query failed:', err);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
    }
  };

  const hasValidQuery = query.trim().length > 0;
  const canSubmit = hasValidQuery && !isLoading;

  return (
    <VStack spacing={6} align="stretch" w="full">
      {/* Query Input */}
      <Box
        bg={bgColor}
        border="1px solid"
        borderColor={borderColor}
        borderRadius="lg"
        p={6}
        shadow="sm"
      >
        <VStack spacing={4} align="stretch">
          <FormControl>
            <FormLabel fontSize="sm" fontWeight="semibold">
              Ask a question about weather data
            </FormLabel>
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="e.g., What are the weather patterns for New York over the last week?"
              size="lg"
              rows={3}
              resize="vertical"
            />
            <Text fontSize="xs" color={textColor} mt={1}>
              Press Ctrl+Enter to submit
            </Text>
          </FormControl>

          {/* Settings Toggle */}
          <HStack justify="space-between" align="center">
            <Button
              leftIcon={<Settings size={16} />}
              variant="ghost"
              size="sm"
              onClick={() => setShowSettings(!showSettings)}
            >
              {showSettings ? 'Hide' : 'Show'} Settings
            </Button>

            <Button
              leftIcon={<Send size={16} />}
              onClick={handleSubmit}
              isLoading={isLoading}
              loadingText="Querying..."
              colorScheme="blue"
              isDisabled={!canSubmit}
            >
              Ask Question
            </Button>
          </HStack>

          {/* Advanced Settings */}
          {showSettings && (
            <Box
              bg={useColorModeValue('gray.50', 'gray.700')}
              borderRadius="md"
              p={4}
              border="1px solid"
              borderColor={borderColor}
            >
              <VStack spacing={4} align="stretch">
                <Text fontSize="sm" fontWeight="semibold">
                  Query Settings
                </Text>

                <HStack justify="space-between">
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="streaming" mb="0" fontSize="sm">
                      Streaming Response
                    </FormLabel>
                    <Switch
                      id="streaming"
                      isChecked={streaming}
                      onChange={(e) => setStreaming(e.target.checked)}
                      size="sm"
                    />
                  </FormControl>

                  <Badge colorScheme="blue" variant="outline">
                    {streaming ? 'Real-time' : 'Standard'}
                  </Badge>
                </HStack>

                <FormControl>
                  <FormLabel fontSize="sm">
                    Max Sources: {maxSources}
                  </FormLabel>
                  <Slider
                    value={maxSources}
                    onChange={setMaxSources}
                    min={1}
                    max={10}
                    step={1}
                  >
                    <SliderTrack>
                      <SliderFilledTrack />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                </FormControl>

                <FormControl>
                  <FormLabel fontSize="sm">
                    Min Similarity: {(minSimilarity * 100).toFixed(0)}%
                  </FormLabel>
                  <Slider
                    value={minSimilarity}
                    onChange={setMinSimilarity}
                    min={0.5}
                    max={1.0}
                    step={0.05}
                  >
                    <SliderTrack>
                      <SliderFilledTrack />
                    </SliderTrack>
                    <SliderThumb />
                  </Slider>
                </FormControl>
              </VStack>
            </Box>
          )}
        </VStack>
      </Box>

      {/* Loading State */}
      {isLoading && (
        <Box textAlign="center" py={8}>
          <VStack spacing={4}>
            <Spinner size="lg" color="blue.500" />
            <Text color={textColor}>
              {streaming ? 'Streaming response...' : 'Processing your question...'}
            </Text>
          </VStack>
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert status="error" borderRadius="lg">
          <AlertIcon />
          <VStack align="start" spacing={2}>
            <Text fontWeight="semibold">Query Failed</Text>
            <Text fontSize="sm">
              {error instanceof Error ? error.message : 'An unexpected error occurred'}
            </Text>
          </VStack>
        </Alert>
      )}

      {/* Results */}
      {result && !isLoading && (
        <VStack spacing={6} align="stretch">
          {/* Answer */}
          <Box
            bg={bgColor}
            border="1px solid"
            borderColor={borderColor}
            borderRadius="lg"
            p={6}
            shadow="sm"
          >
            <VStack align="stretch" spacing={4}>
              <HStack justify="space-between" align="center">
                <Text fontSize="lg" fontWeight="semibold" color="green.500">
                  Answer
                </Text>
                <Badge colorScheme="green" variant="subtle">
                  {result.sources.length} sources
                </Badge>
              </HStack>
              
              <Text color={textColor} lineHeight="1.6" whiteSpace="pre-wrap">
                {result.answer}
              </Text>
            </VStack>
          </Box>

          {/* Sources */}
          {result.sources.length > 0 && (
            <Box>
              <Text fontSize="lg" fontWeight="semibold" mb={4} color="blue.500">
                Sources
              </Text>
              <VStack spacing={3} align="stretch">
                {result.sources.map((source, index) => (
                  <RagSourceCard key={source.source_id} source={source} index={index} />
                ))}
              </VStack>
            </Box>
          )}

          {/* Metadata */}
          {result.metadata && Object.keys(result.metadata).length > 0 && (
            <Box
              bg={useColorModeValue('gray.50', 'gray.700')}
              borderRadius="lg"
              p={4}
              border="1px solid"
              borderColor={borderColor}
            >
              <Text fontSize="sm" fontWeight="semibold" mb={2}>
                Query Metadata
              </Text>
              <Text fontSize="xs" color={textColor}>
                {JSON.stringify(result.metadata, null, 2)}
              </Text>
            </Box>
          )}
        </VStack>
      )}

      {/* Empty State */}
      {!result && !isLoading && !error && (
        <Box textAlign="center" py={12}>
          <VStack spacing={4}>
            <Text fontSize="lg" color={textColor}>
              Ask a question to get started
            </Text>
            <Text color="gray.400" fontSize="sm">
              The RAG system will search through weather documents and provide intelligent answers
            </Text>
          </VStack>
        </Box>
      )}
    </VStack>
  );
};

export default RagQueryInterface;