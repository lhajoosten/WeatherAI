// RAG Chat demo page

import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Alert,
  AlertIcon,
  Badge,
  HStack,
} from '@chakra-ui/react';

import { ChatShell } from '../components/ChatShell';

import { ErrorBoundary } from '@/shared/ui/error/ErrorBoundary';
import { useFeatureFlags } from '@/shared/config/flags';

export function RagDemoPage() {
  const flags = useFeatureFlags();

  return (
    <ErrorBoundary>
      <Container maxW="4xl" py={8}>
        <VStack spacing={6} align="stretch">
          {/* Header */}
          <Box textAlign="center">
            <HStack justify="center" mb={4}>
              <Heading size="lg">Weather AI Assistant</Heading>
              <Badge colorScheme={flags.rag.enabled ? 'green' : 'red'} variant="solid">
                {flags.rag.enabled ? 'Enabled' : 'Disabled'}
              </Badge>
            </HStack>
            <Text color="gray.600" maxW="600px" mx="auto">
              Ask questions about weather data and get AI-powered insights. 
              This demo shows streaming responses with mock data.
            </Text>
          </Box>

          {/* Feature Status */}
          {!flags.rag.enabled && (
            <Alert status="warning">
              <AlertIcon />
              RAG feature is disabled. Set <code>VITE_FEATURE_RAG=1</code> in your environment to enable it.
            </Alert>
          )}

          {/* Chat Interface */}
          <Box>
            <ChatShell 
              placeholder="Ask me about weather patterns, forecasts, or climate data..."
              onMessage={(message) => {
                console.log('New message:', message);
              }}
            />
          </Box>

          {/* Demo Instructions */}
          <Alert status="info">
            <AlertIcon />
            <Box>
              <Text fontWeight="bold">Demo Features:</Text>
              <Text fontSize="sm" mt={1}>
                • Streaming responses with realistic typing simulation<br/>
                • Message history with timestamps<br/>
                • Source citations placeholder<br/>
                • Error handling and loading states<br/>
                • Accessibility features (ARIA live regions)
              </Text>
            </Box>
          </Alert>
        </VStack>
      </Container>
    </ErrorBoundary>
  );
}