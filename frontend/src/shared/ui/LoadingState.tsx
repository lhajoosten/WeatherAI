import { VStack, Spinner, Text } from '@chakra-ui/react';
import React from 'react';

import { useT } from '@/shared/i18n';

export interface LoadingStateProps {
  message?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}

/**
 * LoadingState component for displaying loading indicators
 */
export const LoadingState: React.FC<LoadingStateProps> = ({ 
  message,
  size = 'md'
}) => {
  const t = useT();

  return (
    <VStack spacing={4} p={6} textAlign="center">
      <Spinner size={size} color="blue.500" />
      <Text color="gray.600">
        {message || t('common.loading')}
      </Text>
    </VStack>
  );
};