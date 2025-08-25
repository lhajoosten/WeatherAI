import { Box, Heading, Text, VStack } from '@chakra-ui/react';
import React from 'react';

const AnalyticsPage: React.FC = () => {
  return (
    <Box p={8} maxW="4xl" mx="auto" mt={8}>
      <VStack spacing={6} align="center">
        <Heading size="lg" color="primary.600">
          Analytics Dashboard
        </Heading>
        <Text textAlign="center" color="gray.600">
          Weather analytics, charts, and data visualization will be migrated here in PR2/PR3.
          This includes historical data analysis, trends, and performance metrics.
        </Text>
        <Text fontSize="sm" color="gray.500">
          Route: /analytics
        </Text>
      </VStack>
    </Box>
  );
};

export default AnalyticsPage;