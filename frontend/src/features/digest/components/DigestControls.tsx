import React, { useState } from 'react';
import {
  Box,
  Button,
  Input,
  FormControl,
  FormLabel,
  HStack,
  VStack,
  Text,
  useColorModeValue,
  Icon,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { Calendar, RefreshCw } from 'react-feather';
import { format, subDays } from 'date-fns';

interface DigestControlsProps {
  selectedDate?: string;
  onDateChange: (date: string) => void;
  onRegenerate: (force?: boolean) => void;
  isRegenerating: boolean;
  isStale?: boolean;
}

const DigestControls: React.FC<DigestControlsProps> = ({
  selectedDate,
  onDateChange,
  onRegenerate,
  isRegenerating,
  isStale = false,
}) => {
  const [inputDate, setInputDate] = useState(selectedDate || '');
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Format date for input (YYYY-MM-DD)
  const formatDateForInput = (date: Date): string => {
    return format(date, 'yyyy-MM-dd');
  };

  const handleDateChange = (dateString: string) => {
    setInputDate(dateString);
    onDateChange(dateString);
  };

  const setToday = () => {
    const today = formatDateForInput(new Date());
    handleDateChange(today);
  };

  const setYesterday = () => {
    const yesterday = formatDateForInput(subDays(new Date(), 1));
    handleDateChange(yesterday);
  };

  const handleRegenerate = () => {
    onRegenerate(true);
  };

  return (
    <Box
      bg={bgColor}
      border="1px solid"
      borderColor={borderColor}
      borderRadius="lg"
      p={4}
      shadow="sm"
    >
      <VStack spacing={4} align="stretch">
        {/* Stale Alert */}
        {isStale && (
          <Alert status="warning" borderRadius="md" size="sm">
            <AlertIcon />
            <Text fontSize="sm">
              This digest is more than 4 hours old. Consider regenerating for the latest data.
            </Text>
          </Alert>
        )}

        {/* Date Selection */}
        <VStack spacing={3} align="stretch">
          <FormControl>
            <FormLabel fontSize="sm" mb={2}>
              <HStack spacing={2}>
                <Icon as={Calendar} size={16} />
                <Text>Date</Text>
              </HStack>
            </FormLabel>
            <Input
              type="date"
              value={inputDate}
              onChange={(e) => handleDateChange(e.target.value)}
              size="sm"
            />
          </FormControl>

          {/* Quick Date Buttons */}
          <HStack spacing={2}>
            <Button
              size="xs"
              variant="outline"
              onClick={setToday}
              colorScheme="blue"
            >
              Today
            </Button>
            <Button
              size="xs"
              variant="outline"
              onClick={setYesterday}
              colorScheme="gray"
            >
              Yesterday
            </Button>
          </HStack>
        </VStack>

        {/* Actions */}
        <VStack spacing={2} align="stretch">
          <Button
            leftIcon={<RefreshCw size={16} />}
            onClick={handleRegenerate}
            isLoading={isRegenerating}
            loadingText="Regenerating..."
            size="sm"
            colorScheme="blue"
            variant="outline"
          >
            Regenerate Digest
          </Button>
          
          <Text fontSize="xs" color="gray.500" textAlign="center">
            Force regeneration with latest weather data
          </Text>
        </VStack>
      </VStack>
    </Box>
  );
};

export default DigestControls;