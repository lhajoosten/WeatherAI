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
} from '@chakra-ui/react';
import { ExternalLink, Hash } from 'react-feather';
import type { SourceDTO } from '@/shared/types/api';

interface RagSourceCardProps {
  source: SourceDTO;
  index: number;
}

const RagSourceCard: React.FC<RagSourceCardProps> = ({ source, index }) => {
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'yellow';
    return 'orange';
  };

  return (
    <Box
      bg={bgColor}
      border="1px solid"
      borderColor={borderColor}
      borderRadius="lg"
      p={4}
      w="full"
      _hover={{ shadow: 'md' }}
      transition="all 0.2s"
    >
      <VStack align="stretch" spacing={3}>
        {/* Header */}
        <HStack justify="space-between" align="center">
          <HStack spacing={2}>
            <Icon as={Hash} size={16} color="blue.500" />
            <Text fontSize="sm" fontWeight="semibold">
              Source {index + 1}
            </Text>
          </HStack>
          
          <Badge colorScheme={getScoreColor(source.score)} variant="subtle">
            {(source.score * 100).toFixed(1)}% match
          </Badge>
        </HStack>

        {/* Content Preview */}
        {source.content_preview && (
          <Box>
            <Text fontSize="sm" color={textColor} lineHeight="1.5">
              {source.content_preview}
            </Text>
          </Box>
        )}

        {/* Source ID */}
        <Flex justify="space-between" align="center" fontSize="xs" color={textColor}>
          <Text>ID: {source.source_id}</Text>
          
          <HStack spacing={1}>
            <Icon as={ExternalLink} size={12} />
            <Text>Document</Text>
          </HStack>
        </Flex>
      </VStack>
    </Box>
  );
};

export default RagSourceCard;