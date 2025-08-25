import { Box, Heading, Text, VStack } from '@chakra-ui/react';
import React from 'react';

const RagPage: React.FC = () => {
  return (
    <Box p={8} maxW="4xl" mx="auto" mt={8}>
      <VStack spacing={6} align="center">
        <Heading size="lg" color="primary.600">
          RAG Knowledge Base
        </Heading>
        <Text textAlign="center" color="gray.600">
          Retrieval-Augmented Generation features will be implemented here in PR2/PR3.
          This includes knowledge base queries, document search, and AI-powered Q&A.
        </Text>
        <Text fontSize="sm" color="gray.500">
          Route: /rag
        </Text>
      </VStack>
    </Box>
  );
};

export default RagPage;