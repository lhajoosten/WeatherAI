import { VStack, Text, Button } from '@chakra-ui/react';
import React from 'react';

import { useT } from '@/shared/i18n';
import { AppError } from '@/shared/types';

export interface ErrorStateProps {
  error: AppError;
  onRetry?: () => void;
  showRetry?: boolean;
}

/**
 * ErrorState component for displaying errors with optional retry
 */
export const ErrorState: React.FC<ErrorStateProps> = ({ 
  error, 
  onRetry,
  showRetry = true 
}) => {
  const t = useT();

  const getErrorMessage = (error: AppError): string => {
    switch (error.kind) {
      case 'network':
        return t('errors.network');
      case 'server':
        return t('errors.server');
      case 'client':
        return t('errors.client');
      case 'timeout':
        return t('errors.timeout');
      default:
        return error.message || t('errors.unknown');
    }
  };

  return (
    <VStack spacing={4} p={6} textAlign="center">
      <Text fontSize="lg" fontWeight="semibold" color="red.500">
        {t('common.error')}
      </Text>
      <Text color="gray.600">
        {getErrorMessage(error)}
      </Text>
      {showRetry && onRetry && (
        <Button
          onClick={onRetry}
          variant="outline"
          colorScheme="red"
          size="sm"
        >
          {t('common.retry')}
        </Button>
      )}
    </VStack>
  );
};