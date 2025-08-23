import React from 'react';
import {
  Box,
  Text,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  useColorModeValue,
  Flex,
  Icon
} from '@chakra-ui/react';
import { TrendingUp, TrendingDown, Minus } from 'react-feather';

interface TrendDeltaCardProps {
  title: string;
  currentValue: number | null;
  previousValue: number | null;
  delta: number | null;
  pctChange: number | null;
  unit?: string;
  precision?: number;
  isLoading?: boolean;
}

const TrendDeltaCard: React.FC<TrendDeltaCardProps> = ({
  title,
  currentValue,
  previousValue,
  delta,
  pctChange,
  unit = '',
  precision = 1,
  isLoading = false
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const textColor = useColorModeValue('gray.600', 'gray.300');

  const formatValue = (value: number | null): string => {
    if (value === null) return 'N/A';
    return value.toFixed(precision);
  };

  const getTrendColor = (change: number | null): string => {
    if (change === null || change === 0) return 'gray.500';
    return change > 0 ? 'green.500' : 'red.500';
  };

  const getTrendIcon = (change: number | null) => {
    if (change === null || change === 0) return Minus;
    return change > 0 ? TrendingUp : TrendingDown;
  };

  const getTrendDirection = (change: number | null): 'increase' | 'decrease' | undefined => {
    if (change === null || change === 0) return undefined;
    return change > 0 ? 'increase' : 'decrease';
  };

  if (isLoading) {
    return (
      <Box
        bg={bgColor}
        border="1px solid"
        borderColor={borderColor}
        borderRadius="lg"
        p={6}
        shadow="sm"
        _hover={{ shadow: 'md' }}
        transition="shadow 0.2s"
      >
        <Stat>
          <StatLabel color={textColor}>{title}</StatLabel>
          <StatNumber>Loading...</StatNumber>
        </Stat>
      </Box>
    );
  }

  return (
    <Box
      bg={bgColor}
      border="1px solid"
      borderColor={borderColor}
      borderRadius="lg"
      p={6}
      shadow="sm"
      _hover={{ shadow: 'md' }}
      transition="shadow 0.2s"
    >
      <Stat>
        <StatLabel color={textColor} fontSize="sm" fontWeight="medium">
          {title}
        </StatLabel>
        
        <StatNumber fontSize="2xl" fontWeight="bold">
          {formatValue(currentValue)}{unit}
        </StatNumber>
        
        {delta !== null && pctChange !== null && (
          <StatHelpText mb={0}>
            <Flex align="center" gap={1}>
              <StatArrow type={getTrendDirection(delta)} />
              <Text fontSize="sm">
                {formatValue(Math.abs(delta))}{unit} ({Math.abs(pctChange).toFixed(1)}%)
              </Text>
            </Flex>
          </StatHelpText>
        )}
        
        {previousValue !== null && (
          <Text fontSize="xs" color={textColor} mt={2}>
            Previous: {formatValue(previousValue)}{unit}
          </Text>
        )}
        
        {delta !== null && (
          <Flex align="center" gap={1} mt={2}>
            <Icon 
              as={getTrendIcon(delta)} 
              color={getTrendColor(delta)} 
              boxSize={4}
            />
            <Text fontSize="xs" color={getTrendColor(delta)} fontWeight="medium">
              {delta === 0 ? 'No change' : 
               delta > 0 ? `+${formatValue(delta)}${unit}` : 
               `${formatValue(delta)}${unit}`}
            </Text>
          </Flex>
        )}
      </Stat>
    </Box>
  );
};

export default TrendDeltaCard;