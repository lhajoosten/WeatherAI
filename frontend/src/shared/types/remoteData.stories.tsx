import { VStack, Text, Code, Badge, Button, Box } from '@chakra-ui/react';
import type { Meta, StoryObj } from '@storybook/react';
import React, { useState } from 'react';

import { RemoteData, remoteData, isIdle, isLoading, isSuccess, isError } from './remoteData';

// Mock data for the example
interface WeatherData {
  temperature: number;
  condition: string;
  location: string;
}

const mockWeatherData: WeatherData = {
  temperature: 22,
  condition: 'Sunny',
  location: 'Amsterdam',
};

const mockError = {
  kind: 'network' as const,
  message: 'Failed to fetch weather data',
};

const meta: Meta = {
  title: 'Shared/Types/RemoteData',
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;

// Component to demonstrate RemoteData usage
const RemoteDataDemo: React.FC<{ data: RemoteData<WeatherData> }> = ({ data }) => {
  const getStateColor = () => {
    if (isIdle(data)) return 'gray';
    if (isLoading(data)) return 'blue';
    if (isSuccess(data)) return 'green';
    if (isError(data)) return 'red';
    return 'gray';
  };

  const getStateLabel = () => {
    if (isIdle(data)) return 'Idle';
    if (isLoading(data)) return 'Loading';
    if (isSuccess(data)) return 'Success';
    if (isError(data)) return 'Error';
    return 'Unknown';
  };

  return (
    <VStack spacing={4} align="stretch" minW="300px">
      <Box p={4} border="1px" borderColor="gray.200" borderRadius="md">
        <VStack spacing={3} align="start">
          <Badge colorScheme={getStateColor()} variant="solid">
            State: {getStateLabel()}
          </Badge>
          
          {isIdle(data) && (
            <Text color="gray.600">No data requested yet</Text>
          )}
          
          {isLoading(data) && (
            <Text color="blue.600">Loading weather data...</Text>
          )}
          
          {isSuccess(data) && (
            <VStack align="start" spacing={2}>
              <Text fontWeight="bold">Weather Data:</Text>
              <Code p={2} borderRadius="md">
                {JSON.stringify(data.data, null, 2)}
              </Code>
            </VStack>
          )}
          
          {isError(data) && (
            <VStack align="start" spacing={2}>
              <Text color="red.600" fontWeight="bold">Error occurred:</Text>
              <Code p={2} borderRadius="md" colorScheme="red">
                {JSON.stringify(data.error, null, 2)}
              </Code>
            </VStack>
          )}
        </VStack>
      </Box>
    </VStack>
  );
};

// Interactive story with controls
const InteractiveRemoteData: React.FC = () => {
  const [currentState, setCurrentState] = useState<RemoteData<WeatherData>>(remoteData.idle());

  return (
    <VStack spacing={6} align="stretch">
      <Text fontSize="lg" fontWeight="bold">
        Interactive RemoteData State Demo
      </Text>
      
      <Box>
        <Text mb={3} fontWeight="medium">Control the state:</Text>
        <VStack spacing={2} align="start">
          <Button size="sm" onClick={() => setCurrentState(remoteData.idle())}>
            Set Idle
          </Button>
          <Button size="sm" onClick={() => setCurrentState(remoteData.loading())}>
            Set Loading
          </Button>
          <Button size="sm" onClick={() => setCurrentState(remoteData.success(mockWeatherData))}>
            Set Success
          </Button>
          <Button size="sm" onClick={() => setCurrentState(remoteData.error(mockError))}>
            Set Error
          </Button>
        </VStack>
      </Box>
      
      <RemoteDataDemo data={currentState} />
    </VStack>
  );
};

export const Interactive: StoryObj = {
  render: () => <InteractiveRemoteData />,
};

export const States: StoryObj = {
  render: () => (
    <VStack spacing={6} align="stretch">
      <Text fontSize="lg" fontWeight="bold">
        All RemoteData States
      </Text>
      
      <VStack spacing={4} align="stretch">
        <Box>
          <Text fontWeight="medium" mb={2}>Idle State:</Text>
          <RemoteDataDemo data={remoteData.idle<WeatherData>()} />
        </Box>
        
        <Box>
          <Text fontWeight="medium" mb={2}>Loading State:</Text>
          <RemoteDataDemo data={remoteData.loading<WeatherData>()} />
        </Box>
        
        <Box>
          <Text fontWeight="medium" mb={2}>Success State:</Text>
          <RemoteDataDemo data={remoteData.success(mockWeatherData)} />
        </Box>
        
        <Box>
          <Text fontWeight="medium" mb={2}>Error State:</Text>
          <RemoteDataDemo data={remoteData.error(mockError)} />
        </Box>
      </VStack>
    </VStack>
  ),
};