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
  useColorModeValue,
  FormControl,
  FormLabel,
  Input,
  Progress,
  Badge,
  useToast,
} from '@chakra-ui/react';
import { Upload, FileText, Check } from 'react-feather';
import { ragService } from '@/shared/api/services';
import { useMutation } from '@tanstack/react-query';
import type { IngestRequest, IngestResponse } from '@/shared/types/api';

const RagIngestInterface: React.FC = () => {
  const [sourceId, setSourceId] = useState('');
  const [text, setText] = useState('');
  const [metadata, setMetadata] = useState('{}');
  const [result, setResult] = useState<IngestResponse | null>(null);

  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  const ingestMutation = useMutation({
    mutationFn: (data: IngestRequest) => ragService.ingestDocument(data),
    onSuccess: (data) => {
      setResult(data);
      toast({
        title: 'Document ingested successfully',
        description: `Created ${data.chunks} chunks`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    },
    onError: (error) => {
      toast({
        title: 'Ingestion failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
  });

  const handleIngest = async () => {
    if (!sourceId.trim() || !text.trim()) {
      toast({
        title: 'Missing required fields',
        description: 'Please provide both source ID and text content',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    let parsedMetadata = {};
    try {
      if (metadata.trim()) {
        parsedMetadata = JSON.parse(metadata);
      }
    } catch (error) {
      toast({
        title: 'Invalid metadata',
        description: 'Metadata must be valid JSON',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    await ingestMutation.mutateAsync({
      source_id: sourceId,
      text,
      metadata: parsedMetadata,
    });
  };

  const handleReset = () => {
    setSourceId('');
    setText('');
    setMetadata('{}');
    setResult(null);
    ingestMutation.reset();
  };

  const canSubmit = sourceId.trim() && text.trim() && !ingestMutation.isPending;

  return (
    <VStack spacing={6} align="stretch" w="full">
      {/* Ingest Form */}
      <Box
        bg={bgColor}
        border="1px solid"
        borderColor={borderColor}
        borderRadius="lg"
        p={6}
        shadow="sm"
      >
        <VStack spacing={4} align="stretch">
          <HStack justify="space-between" align="center">
            <Text fontSize="lg" fontWeight="semibold">
              Ingest Document
            </Text>
            <Badge colorScheme="blue" variant="outline">
              RAG Knowledge Base
            </Badge>
          </HStack>

          <FormControl>
            <FormLabel fontSize="sm" fontWeight="semibold">
              Source ID
            </FormLabel>
            <Input
              value={sourceId}
              onChange={(e) => setSourceId(e.target.value)}
              placeholder="e.g., weather-report-2024-01-15"
              size="sm"
            />
            <Text fontSize="xs" color={textColor} mt={1}>
              Unique identifier for this document
            </Text>
          </FormControl>

          <FormControl>
            <FormLabel fontSize="sm" fontWeight="semibold">
              Document Content
            </FormLabel>
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your weather document content here..."
              size="sm"
              rows={8}
              resize="vertical"
            />
            <Text fontSize="xs" color={textColor} mt={1}>
              The text content will be processed and split into searchable chunks
            </Text>
          </FormControl>

          <FormControl>
            <FormLabel fontSize="sm" fontWeight="semibold">
              Metadata (JSON)
            </FormLabel>
            <Textarea
              value={metadata}
              onChange={(e) => setMetadata(e.target.value)}
              placeholder='{"type": "weather_report", "date": "2024-01-15", "location": "New York"}'
              size="sm"
              rows={3}
              fontFamily="mono"
              fontSize="xs"
            />
            <Text fontSize="xs" color={textColor} mt={1}>
              Optional metadata in JSON format
            </Text>
          </FormControl>

          <HStack justify="space-between" align="center" pt={2}>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              isDisabled={ingestMutation.isPending}
            >
              Reset
            </Button>

            <Button
              leftIcon={<Upload size={16} />}
              onClick={handleIngest}
              isLoading={ingestMutation.isPending}
              loadingText="Ingesting..."
              colorScheme="green"
              isDisabled={!canSubmit}
            >
              Ingest Document
            </Button>
          </HStack>
        </VStack>
      </Box>

      {/* Progress */}
      {ingestMutation.isPending && (
        <Box>
          <Text fontSize="sm" mb={2} color={textColor}>
            Processing document...
          </Text>
          <Progress isIndeterminate colorScheme="green" size="sm" borderRadius="md" />
        </Box>
      )}

      {/* Success Result */}
      {result && !ingestMutation.isPending && !ingestMutation.isError && (
        <Alert status="success" borderRadius="lg">
          <AlertIcon />
          <VStack align="start" spacing={2}>
            <HStack spacing={2}>
              <Check size={16} />
              <Text fontWeight="semibold">Document ingested successfully</Text>
            </HStack>
            <VStack align="start" spacing={1} fontSize="sm">
              <Text>Document ID: {result.document_id}</Text>
              <Text>Chunks created: {result.chunks}</Text>
              <Text>Status: {result.status}</Text>
            </VStack>
          </VStack>
        </Alert>
      )}

      {/* Error State */}
      {ingestMutation.isError && (
        <Alert status="error" borderRadius="lg">
          <AlertIcon />
          <VStack align="start" spacing={2}>
            <Text fontWeight="semibold">Ingestion Failed</Text>
            <Text fontSize="sm">
              {ingestMutation.error instanceof Error 
                ? ingestMutation.error.message 
                : 'An unexpected error occurred'}
            </Text>
          </VStack>
        </Alert>
      )}

      {/* Help Information */}
      <Box
        bg={useColorModeValue('blue.50', 'blue.900')}
        borderRadius="lg"
        p={4}
        border="1px solid"
        borderColor={useColorModeValue('blue.200', 'blue.700')}
      >
        <VStack spacing={2} align="start">
          <HStack spacing={2}>
            <FileText size={16} />
            <Text fontSize="sm" fontWeight="semibold" color="blue.600">
              About Document Ingestion
            </Text>
          </HStack>
          <Text fontSize="sm" color={textColor}>
            Documents are automatically processed, cleaned, and split into chunks for efficient retrieval.
            Each chunk is embedded using AI and stored in the vector database for similarity search.
          </Text>
          <HStack spacing={4} fontSize="xs" color="gray.500">
            <Text>• Supports various text formats</Text>
            <Text>• Automatic chunk optimization</Text>
            <Text>• Metadata enrichment</Text>
          </HStack>
        </VStack>
      </Box>
    </VStack>
  );
};

export default RagIngestInterface;