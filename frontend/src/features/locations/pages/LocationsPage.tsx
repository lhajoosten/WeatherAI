import { Box, Heading, Text, VStack } from '@chakra-ui/react';
import React from 'react';

const LocationsPage: React.FC = () => {
  return (
    <Box p={8} maxW="4xl" mx="auto" mt={8}>
      <VStack spacing={6} align="center">
        <Heading size="lg" color="primary.600">
          Locations Management
        </Heading>
        <Text textAlign="center" color="gray.600">
          Location management, maps, and geographic features will be migrated here in PR2/PR3.
          This includes location CRUD, groups, maps integration, and geocoding.
        </Text>
        <Text fontSize="sm" color="gray.500">
          Route: /locations
        </Text>
      </VStack>
    </Box>
  );
};

export default LocationsPage;