import { Skeleton as ChakraSkeleton, SkeletonProps as ChakraSkeletonProps, VStack, HStack } from '@chakra-ui/react';
import React from 'react';

export interface SkeletonProps extends ChakraSkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular';
  lines?: number;
}

/**
 * Skeleton component for loading states
 */
export const Skeleton: React.FC<SkeletonProps> = ({ 
  variant = 'text',
  lines = 1,
  ...props 
}) => {
  if (variant === 'circular') {
    return (
      <ChakraSkeleton
        borderRadius="full"
        {...props}
      />
    );
  }

  if (variant === 'text' && lines > 1) {
    return (
      <VStack spacing={2} align="stretch">
        {Array.from({ length: lines }).map((_, index) => (
          <ChakraSkeleton
            key={index}
            height="20px"
            {...props}
          />
        ))}
      </VStack>
    );
  }

  return (
    <ChakraSkeleton
      {...props}
    />
  );
};

/**
 * Predefined skeleton layouts for common use cases
 */
export const SkeletonCard: React.FC = () => (
  <VStack spacing={3} align="stretch">
    <HStack spacing={3}>
      <Skeleton variant="circular" width="40px" height="40px" />
      <VStack spacing={1} align="stretch" flex={1}>
        <Skeleton height="16px" width="60%" />
        <Skeleton height="14px" width="40%" />
      </VStack>
    </HStack>
    <Skeleton lines={3} />
  </VStack>
);

export const SkeletonText: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
  <Skeleton variant="text" lines={lines} />
);