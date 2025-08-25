import { Box, Heading, Text, VStack } from '@chakra-ui/react';
import React from 'react';

const DigestPage: React.FC = () => {
  return (
    <Box p={8} maxW="4xl" mx="auto" mt={8}>
      <VStack spacing={6} align="center">
        <Heading size="lg" color="primary.600">
          Weather Digest
        </Heading>
        <Text textAlign="center" color="gray.600">
          AI-powered weather summaries and insights will be implemented here in PR2/PR3.
          This includes weather digest generation, personalized recommendations, and explanations.
        </Text>
        <Text fontSize="sm" color="gray.500">
          Route: /digest
        </Text>
      </VStack>
    </Box>
  );
};

export default DigestPage;