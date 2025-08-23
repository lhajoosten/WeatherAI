import React from 'react';
import {
  Box,
  Text,
  Button,
  Spinner,
  Alert,
  AlertIcon,
  VStack,
  HStack,
  Badge,
  useColorModeValue,
  Divider
} from '@chakra-ui/react';
import { RefreshCw } from 'react-feather';
import { useAnalyticsSummary, AnalyticsSummaryRequest } from '../hooks/useAnalytics';

interface AnalyticsSummaryProps {
  locationId: number;
  period: '7d' | '30d';
  metrics: string[];
  onRefresh?: () => void;
}

const AnalyticsSummary: React.FC<AnalyticsSummaryProps> = ({
  locationId,
  period,
  metrics,
  onRefresh
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');
  
  const summaryMutation = useAnalyticsSummary();

  const handleGenerate = () => {
    const request: AnalyticsSummaryRequest = {
      location_id: locationId,
      period,
      metrics
    };
    
    summaryMutation.mutate(request);
    onRefresh?.();
  };

  const parseNarrative = (narrative: string) => {
    // Parse the structured narrative into sections
    const sections = narrative.split('\n\n').filter(section => section.trim());
    
    return sections.map(section => {
      const lines = section.split('\n');
      const title = lines[0]?.replace(/^\d+\.\s*/, '').replace(':', '');
      const content = lines.slice(1).join(' ').trim();
      
      return {
        title: title || 'Summary',
        content: content || section
      };
    });
  };

  return (
    <Box
      bg={bgColor}
      border="1px solid"
      borderColor={borderColor}
      borderRadius="lg"
      p={6}
      shadow="sm"
    >
      <HStack justify="space-between" align="center" mb={4}>
        <Text fontSize="lg" fontWeight="semibold">
          AI Analytics Summary
        </Text>
        <Button
          leftIcon={<RefreshCw size={16} />}
          onClick={handleGenerate}
          isLoading={summaryMutation.isPending}
          loadingText="Generating..."
          size="sm"
          colorScheme="blue"
          variant="outline"
        >
          Generate
        </Button>
      </HStack>

      {summaryMutation.isPending && (
        <VStack spacing={4} py={8}>
          <Spinner color="blue.500" size="lg" />
          <Text color={textColor}>Analyzing weather data...</Text>
        </VStack>
      )}

      {summaryMutation.isError && (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          Failed to generate summary. Please try again.
        </Alert>
      )}

      {summaryMutation.isSuccess && summaryMutation.data && (
        <VStack align="stretch" spacing={4}>
          {/* Metadata */}
          <HStack spacing={2} wrap="wrap">
            <Badge colorScheme="blue" variant="subtle">
              {period} analysis
            </Badge>
            <Badge colorScheme="green" variant="subtle">
              {summaryMutation.data.model}
            </Badge>
            <Badge colorScheme="purple" variant="subtle">
              {summaryMutation.data.tokens_in + summaryMutation.data.tokens_out} tokens
            </Badge>
          </HStack>

          <Divider />

          {/* Narrative content */}
          <VStack align="stretch" spacing={4}>
            {parseNarrative(summaryMutation.data.narrative).map((section, index) => (
              <Box key={index}>
                <Text fontWeight="semibold" color="blue.500" mb={2}>
                  {section.title}
                </Text>
                <Text color={textColor} fontSize="sm" lineHeight="1.6">
                  {section.content}
                </Text>
              </Box>
            ))}
          </VStack>

          {/* Footer */}
          <Divider />
          <Text fontSize="xs" color={textColor} textAlign="center">
            Generated at {new Date(summaryMutation.data.generated_at).toLocaleString()} • 
            Version {summaryMutation.data.prompt_version}
          </Text>
        </VStack>
      )}

      {!summaryMutation.isPending && !summaryMutation.isSuccess && !summaryMutation.isError && (
        <VStack spacing={4} py={8}>
          <Text color={textColor} textAlign="center">
            Click "Generate" to create an AI-powered analytics summary
          </Text>
          <Text fontSize="sm" color={textColor} textAlign="center">
            Analyzes trends, accuracy metrics, and recent data for insights
          </Text>
        </VStack>
      )}
    </Box>
  );
};

export default AnalyticsSummary;