import { Alert, AlertIcon, AlertTitle, AlertDescription, Box, Button, VStack } from '@chakra-ui/react';
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Box p={8} maxW="md" mx="auto" mt={16}>
          <Alert status="error" flexDirection="column" alignItems="center" textAlign="center" borderRadius="md">
            <AlertIcon boxSize="40px" mr={0} />
            <AlertTitle mt={4} mb={1} fontSize="lg">
              Something went wrong!
            </AlertTitle>
            <AlertDescription maxWidth="sm">
              <VStack spacing={4}>
                <Box>
                  An unexpected error occurred. Please try refreshing the page or contact support if the problem persists.
                </Box>
                {this.state.error && import.meta.env.DEV && (
                  <Box as="pre" fontSize="sm" textAlign="left" bg="gray.100" p={2} borderRadius="md" overflow="auto">
                    {this.state.error.message}
                  </Box>
                )}
                <Button colorScheme="blue" onClick={this.handleReset}>
                  Try Again
                </Button>
              </VStack>
            </AlertDescription>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;