import React from 'react';
import {
  Box,
  Text,
  VStack,
  HStack,
  Badge,
  useColorModeValue,
  Icon,
  Flex,
  Divider,
} from '@chakra-ui/react';
import { Calendar, Clock, Cpu, Hash, Zap } from 'react-feather';
import type { DigestResponse } from '@/shared/types/api';

interface DigestCardProps {
  digest: DigestResponse;
  showMetadata?: boolean;
}

const DigestCard: React.FC<DigestCardProps> = ({ 
  digest, 
  showMetadata = true 
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');
  const highlightColor = useColorModeValue('blue.500', 'blue.300');

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
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
      w="full"
    >
      {/* Header */}
      <VStack align="stretch" spacing={4}>
        <HStack justify="space-between" align="center">
          <HStack spacing={2}>
            <Icon as={Calendar} size={20} color={highlightColor} />
            <Text fontWeight="semibold" fontSize="lg">
              Weather Digest
            </Text>
          </HStack>
          
          <Text fontSize="sm" color={textColor}>
            {formatDate(digest.date)}
          </Text>
        </HStack>

        {/* Summary */}
        <Box>
          <Text fontWeight="medium" mb={3} color={highlightColor}>
            Summary
          </Text>
          <Text color={textColor} lineHeight="1.6">
            {digest.summary}
          </Text>
        </Box>

        {/* Recommendations */}
        {digest.recommendations && digest.recommendations.length > 0 && (
          <Box>
            <Text fontWeight="medium" mb={3} color={highlightColor}>
              Recommendations
            </Text>
            <VStack align="stretch" spacing={2}>
              {digest.recommendations.map((rec, index) => (
                <HStack key={index} spacing={3} align="start">
                  <Icon as={Zap} size={16} color="green.500" mt={0.5} />
                  <Text fontSize="sm" color={textColor}>
                    {rec}
                  </Text>
                </HStack>
              ))}
            </VStack>
          </Box>
        )}

        {/* Highlights */}
        {digest.highlights && digest.highlights.length > 0 && (
          <Box>
            <Text fontWeight="medium" mb={3} color={highlightColor}>
              Key Highlights
            </Text>
            <VStack align="stretch" spacing={2}>
              {digest.highlights.map((highlight, index) => (
                <HStack key={index} spacing={3} align="start">
                  <Icon as={Hash} size={16} color="orange.500" mt={0.5} />
                  <Text fontSize="sm" color={textColor}>
                    {highlight}
                  </Text>
                </HStack>
              ))}
            </VStack>
          </Box>
        )}

        {/* Metadata */}
        {showMetadata && (
          <>
            <Divider />
            <VStack align="stretch" spacing={3}>
              <HStack spacing={4} wrap="wrap">
                <Badge colorScheme="blue" variant="subtle">
                  {digest.tokens_meta.model}
                </Badge>
                <Badge colorScheme="green" variant="subtle">
                  {digest.tokens_meta.input_tokens + digest.tokens_meta.output_tokens} tokens
                </Badge>
                {digest.cache_meta.hit && (
                  <Badge colorScheme="purple" variant="subtle">
                    Cached
                  </Badge>
                )}
              </HStack>

              <Flex justify="space-between" fontSize="xs" color={textColor}>
                <HStack spacing={1}>
                  <Icon as={Clock} size={14} />
                  <Text>Generated at {formatTime(digest.cache_meta.generated_at)}</Text>
                </HStack>
                
                <HStack spacing={1}>
                  <Icon as={Cpu} size={14} />
                  <Text>
                    {digest.tokens_meta.input_tokens}→{digest.tokens_meta.output_tokens} tokens
                  </Text>
                </HStack>
              </Flex>
            </VStack>
          </>
        )}
      </VStack>
    </Box>
  );
};

export default DigestCard;