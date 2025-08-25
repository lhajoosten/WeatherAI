// Streaming indicator component

import { Box, HStack, Text, Spinner } from '@chakra-ui/react';

interface StreamingIndicatorProps {
  isStreaming: boolean;
  label?: string;
}

export function StreamingIndicator({ isStreaming, label = "Assistant is thinking..." }: StreamingIndicatorProps) {
  if (!isStreaming) {
    return null;
  }

  return (
    <HStack spacing={2} align="center" aria-live="polite">
      <Spinner size="sm" color="blue.500" />
      <Text 
        fontSize="sm" 
        color="gray.600"
        sx={{
          animation: `pulse 2s ease-in-out infinite`,
          '@keyframes pulse': {
            '0%': { opacity: 0.4 },
            '50%': { opacity: 1 },
            '100%': { opacity: 0.4 },
          },
        }}
      >
        {label}
      </Text>
      <Box>
        {[0, 1, 2].map((i) => (
          <Box
            key={i}
            as="span"
            display="inline-block"
            w="4px"
            h="4px"
            bg="blue.500"
            borderRadius="full"
            mx="1px"
            sx={{
              animation: `pulse 1.5s ease-in-out infinite`,
              animationDelay: `${i * 0.2}s`,
              '@keyframes pulse': {
                '0%': { opacity: 0.4 },
                '50%': { opacity: 1 },
                '100%': { opacity: 0.4 },
              },
            }}
          />
        ))}
      </Box>
    </HStack>
  );
}