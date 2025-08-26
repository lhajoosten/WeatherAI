// Global error boundary component

import React, { Component, ReactNode } from 'react';
import {
  Box,
  VStack,
  Heading,
  Text,
  Button,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Code,
  useColorModeValue,
} from '@chakra-ui/react';
import { RefreshCw } from 'react-feather';
import { logger } from '@/shared/lib/logger';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // Log error
    logger.error('Error boundary caught error', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });

    // Call custom error handler
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      const { fallback: Fallback } = this.props;
      
      if (Fallback && this.state.error) {
        return <Fallback error={this.state.error} reset={this.handleReset} />;
      }

      return (
        <DefaultErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onReset={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

interface DefaultErrorFallbackProps {
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  onReset: () => void;
}

function DefaultErrorFallback({ error, onReset }: DefaultErrorFallbackProps) {
  const bgColor = useColorModeValue('red.50', 'red.900');
  const isDev = import.meta.env.DEV;

  return (
    <Box
      minH="400px"
      display="flex"
      alignItems="center"
      justifyContent="center"
      p={8}
    >
      <VStack spacing={6} maxW="600px" textAlign="center">
        <Alert status="error" borderRadius="md" bg={bgColor}>
          <AlertIcon />
          <Box>
            <AlertTitle>Something went wrong!</AlertTitle>
            <AlertDescription>
              An unexpected error occurred. Please try refreshing the page.
            </AlertDescription>
          </Box>
        </Alert>

        <VStack spacing={4}>
          <Heading size="md" color="red.500">
            Application Error
          </Heading>
          
          <Text color="gray.600">
            We apologize for the inconvenience. The error has been logged and our team will investigate.
          </Text>

          <Button
            leftIcon={<RefreshCw size={16} />}
            colorScheme="red"
            variant="outline"
            onClick={onReset}
          >
            Try Again
          </Button>

          {isDev && error && (
            <VStack spacing={3} align="stretch" w="full">
              <Text fontWeight="bold" color="red.600">
                Development Error Details:
              </Text>
              <Code p={3} borderRadius="md" fontSize="sm" whiteSpace="pre-wrap">
                {error.message}
              </Code>
              {error.stack && (
                <Code p={3} borderRadius="md" fontSize="xs" whiteSpace="pre-wrap" maxH="200px" overflowY="auto">
                  {error.stack}
                </Code>
              )}
            </VStack>
          )}
        </VStack>
      </VStack>
    </Box>
  );
}

// Hook for triggering error boundary from function components
export function useErrorBoundary() {
  return (error: Error) => {
    throw error;
  };
}