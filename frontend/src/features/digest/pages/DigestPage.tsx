import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  SimpleGrid,
  Flex,
} from '@chakra-ui/react';
import { format } from 'date-fns';
import { useSmartDigest } from '../hooks/useDigest';
import DigestCard from '../components/DigestCard';
import DigestControls from '../components/DigestControls';

const DigestPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('');
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  
  const {
    digest,
    isLoading,
    error,
    isStale,
    regenerate,
    isRegenerating,
  } = useSmartDigest(selectedDate || undefined);

  const handleDateChange = (date: string) => {
    setSelectedDate(date);
  };

  const handleRegenerate = (force: boolean = true) => {
    regenerate(force);
  };

  const getPageTitle = () => {
    if (selectedDate) {
      const date = new Date(selectedDate);
      return `Weather Digest - ${format(date, 'MMMM dd, yyyy')}`;
    }
    return 'Today\'s Weather Digest';
  };

  const getPageSubtitle = () => {
    if (selectedDate) {
      return 'Historical weather digest with AI-powered insights';
    }
    return 'Your personalized morning weather summary with recommendations';
  };

  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        {/* Header */}
        <Box textAlign="center">
          <Heading size="xl" mb={2} color="blue.500">
            {getPageTitle()}
          </Heading>
          <Text color="gray.500" fontSize="lg">
            {getPageSubtitle()}
          </Text>
        </Box>

        {/* Main Content */}
        <SimpleGrid columns={{ base: 1, lg: 4 }} spacing={6}>
          {/* Controls Sidebar */}
          <Box>
            <DigestControls
              selectedDate={selectedDate}
              onDateChange={handleDateChange}
              onRegenerate={handleRegenerate}
              isRegenerating={isRegenerating}
              isStale={isStale}
            />
          </Box>

          {/* Digest Content */}
          <Box gridColumn={{ base: 1, lg: 'span 3' }}>
            {/* Loading State */}
            {isLoading && (
              <Flex justify="center" align="center" py={12}>
                <VStack spacing={4}>
                  <Spinner size="lg" color="blue.500" />
                  <Text color="gray.500">
                    {isRegenerating ? 'Regenerating digest...' : 'Loading digest...'}
                  </Text>
                </VStack>
              </Flex>
            )}

            {/* Error State */}
            {error && !isLoading && (
              <Alert status="error" borderRadius="lg">
                <AlertIcon />
                <VStack align="start" spacing={2}>
                  <Text fontWeight="semibold">Failed to load digest</Text>
                  <Text fontSize="sm">
                    {error instanceof Error ? error.message : 'An unexpected error occurred'}
                  </Text>
                  <Text fontSize="sm" color="gray.500">
                    This could be due to no weather data available for the selected date,
                    or a temporary service issue. Try selecting a different date or regenerating.
                  </Text>
                </VStack>
              </Alert>
            )}

            {/* Digest Content */}
            {digest && !isLoading && (
              <VStack spacing={4} align="stretch">
                <DigestCard digest={digest} showMetadata={true} />
                
                {/* Additional Info */}
                <Box
                  bg={useColorModeValue('blue.50', 'blue.900')}
                  borderRadius="lg"
                  p={4}
                  border="1px solid"
                  borderColor={useColorModeValue('blue.200', 'blue.700')}
                >
                  <VStack spacing={2} align="start">
                    <Text fontSize="sm" fontWeight="semibold" color="blue.600">
                      About Weather Digests
                    </Text>
                    <Text fontSize="sm" color="gray.600">
                      This AI-powered digest analyzes weather patterns, trends, and forecasts 
                      to provide personalized insights and recommendations. Digests are generated 
                      using the latest weather data and are cached for performance.
                    </Text>
                    <HStack spacing={4} fontSize="xs" color="gray.500">
                      <Text>• Updated automatically throughout the day</Text>
                      <Text>• Personalized for your locations</Text>
                      <Text>• Powered by advanced AI analysis</Text>
                    </HStack>
                  </VStack>
                </Box>
              </VStack>
            )}

            {/* No Data State */}
            {!digest && !isLoading && !error && (
              <Box textAlign="center" py={12}>
                <VStack spacing={4}>
                  <Text fontSize="lg" color="gray.500">
                    No digest available
                  </Text>
                  <Text color="gray.400">
                    {selectedDate 
                      ? 'No digest found for the selected date. Try generating one.'
                      : 'Generate your first morning digest to get started.'
                    }
                  </Text>
                </VStack>
              </Box>
            )}
          </Box>
        </SimpleGrid>
      </VStack>
    </Box>
  );
};

export default DigestPage;