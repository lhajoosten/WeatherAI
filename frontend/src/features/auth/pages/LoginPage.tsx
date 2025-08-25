import { Box, Heading, Text, VStack } from '@chakra-ui/react';
import React from 'react';

const LoginPage: React.FC = () => {
  return (
    <Box p={8} maxW="md" mx="auto" mt={16}>
      <VStack spacing={6} align="center">
        <Heading size="lg" color="primary.600">
          Authentication
        </Heading>
        <Text textAlign="center" color="gray.600">
          Login and registration functionality will be implemented in PR2/PR3.
          This is a placeholder page for the auth feature module.
        </Text>
        <Text fontSize="sm" color="gray.500">
          Route: /auth/login
        </Text>
      </VStack>
    </Box>
  );
};

export default LoginPage;