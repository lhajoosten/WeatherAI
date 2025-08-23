import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  SimpleGrid,
  FormControl,
  FormLabel,
  Input,
  Select,
  Alert,
  AlertIcon,
  Spinner,
  Card,
  CardBody,
  Badge,
  useColorModeValue,
  Collapse,
  Divider
} from '@chakra-ui/react';
import { MapPin, Plus, X } from 'react-feather';
import { Location, LocationCreate, ExplainResponse } from '../types/api';
import { useLocation } from '../context/LocationContext';
import api from '../services/apiClient';

const LocationsView: React.FC = () => {
  const { locations, setLocations, selectedLocation, setSelectedLocation } = useLocation();
  const [showAddForm, setShowAddForm] = useState(false);
  const [newLocation, setNewLocation] = useState<LocationCreate>({
    name: '',
    lat: 0,
    lon: 0,
    timezone: 'UTC'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [explainLoading, setExplainLoading] = useState(false);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBgColor = useColorModeValue('white', 'gray.800');

  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      const response = await api.get<Location[]>('/v1/locations');
      setLocations(response.data);
      
      // Auto-select first location if none selected
      if (response.data.length > 0 && !selectedLocation) {
        setSelectedLocation(response.data[0]);
      }
    } catch (err: any) {
      setError('Failed to fetch locations');
    }
  };

  const handleAddLocation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post<Location>('/v1/locations', newLocation);
      const updatedLocations = [...locations, response.data];
      setLocations(updatedLocations);
      setNewLocation({ name: '', lat: 0, lon: 0, timezone: 'UTC' });
      setShowAddForm(false);
      
      // Auto-select the new location if it's the first one
      if (updatedLocations.length === 1) {
        setSelectedLocation(response.data);
      }
    } catch (err: any) {
      setError(err.data?.detail || 'Failed to add location');
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async (locationId: number) => {
    setExplainLoading(true);
    setError('');
    setExplanation(null);

    try {
      const response = await api.post<ExplainResponse>(`/v1/locations/${locationId}/explain`);
      setExplanation(response.data);
    } catch (err: any) {
      setError(err.data?.detail || 'Failed to generate explanation');
    } finally {
      setExplainLoading(false);
    }
  };

  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        {/* Header */}
        <HStack justify="space-between" align="center">
          <VStack align="start" spacing={1}>
            <Heading size="lg">My Locations</Heading>
            <Text color="gray.500">Manage your weather locations</Text>
          </VStack>
          
          <Button
            leftIcon={showAddForm ? <X size={16} /> : <Plus size={16} />}
            onClick={() => setShowAddForm(!showAddForm)}
            colorScheme="blue"
            variant={showAddForm ? "outline" : "solid"}
            isLoading={loading}
          >
            {showAddForm ? 'Cancel' : 'Add Location'}
          </Button>
        </HStack>

        {/* Error display */}
        {error && (
          <Alert status="error" borderRadius="lg">
            <AlertIcon />
            {error}
          </Alert>
        )}

        {/* Add location form */}
        <Collapse in={showAddForm}>
          <Card>
            <CardBody>
              <VStack spacing={4} align="stretch">
                <Heading size="md">Add New Location</Heading>
                
                <form onSubmit={handleAddLocation}>
                  <VStack spacing={4} align="stretch">
                    <FormControl isRequired>
                      <FormLabel>Name</FormLabel>
                      <Input
                        value={newLocation.name}
                        onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })}
                        placeholder="e.g., Home, Office, Seattle"
                        isDisabled={loading}
                      />
                    </FormControl>

                    <HStack spacing={4}>
                      <FormControl isRequired>
                        <FormLabel>Latitude</FormLabel>
                        <Input
                          type="number"
                          value={newLocation.lat}
                          onChange={(e) => setNewLocation({ ...newLocation, lat: parseFloat(e.target.value) })}
                          step="any"
                          min="-90"
                          max="90"
                          isDisabled={loading}
                        />
                      </FormControl>

                      <FormControl isRequired>
                        <FormLabel>Longitude</FormLabel>
                        <Input
                          type="number"
                          value={newLocation.lon}
                          onChange={(e) => setNewLocation({ ...newLocation, lon: parseFloat(e.target.value) })}
                          step="any"
                          min="-180"
                          max="180"
                          isDisabled={loading}
                        />
                      </FormControl>
                    </HStack>

                    <FormControl>
                      <FormLabel>Timezone</FormLabel>
                      <Select
                        value={newLocation.timezone}
                        onChange={(e) => setNewLocation({ ...newLocation, timezone: e.target.value })}
                        isDisabled={loading}
                      >
                        <option value="UTC">UTC</option>
                        <option value="America/New_York">Eastern Time</option>
                        <option value="America/Chicago">Central Time</option>
                        <option value="America/Denver">Mountain Time</option>
                        <option value="America/Los_Angeles">Pacific Time</option>
                        <option value="Europe/London">London</option>
                        <option value="Europe/Paris">Paris</option>
                        <option value="Asia/Tokyo">Tokyo</option>
                      </Select>
                    </FormControl>

                    <Button
                      type="submit"
                      colorScheme="blue"
                      isLoading={loading}
                      loadingText="Adding..."
                    >
                      Add Location
                    </Button>
                  </VStack>
                </form>
              </VStack>
            </CardBody>
          </Card>
        </Collapse>

        {/* Locations grid */}
        {locations.length === 0 ? (
          <Card>
            <CardBody textAlign="center" py={12}>
              <MapPin size={48} style={{ margin: '0 auto 16px' }} color="gray" />
              <Text fontSize="lg" color="gray.500" mb={2}>
                No locations added yet
              </Text>
              <Text color="gray.400">
                Add your first location to get started with weather analytics!
              </Text>
            </CardBody>
          </Card>
        ) : (
          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
            {locations.map((location) => (
              <Card
                key={location.id}
                cursor="pointer"
                border="2px solid"
                borderColor={selectedLocation?.id === location.id ? "blue.500" : "transparent"}
                bg={selectedLocation?.id === location.id ? "blue.50" : cardBgColor}
                _hover={{ shadow: "md" }}
                transition="all 0.2s"
                onClick={() => setSelectedLocation(location)}
              >
                <CardBody>
                  <VStack align="stretch" spacing={4}>
                    <HStack justify="space-between" align="start">
                      <VStack align="start" spacing={1}>
                        <Heading size="md">{location.name}</Heading>
                        <Text fontSize="sm" color="gray.500">
                          {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
                        </Text>
                      </VStack>
                      
                      {selectedLocation?.id === location.id && (
                        <Badge colorScheme="blue" variant="solid">
                          Selected
                        </Badge>
                      )}
                    </HStack>

                    <VStack align="stretch" spacing={2}>
                      <Text fontSize="sm" color="gray.500">
                        Timezone: {location.timezone || 'Not specified'}
                      </Text>
                      <Text fontSize="sm" color="gray.500">
                        Added: {new Date(location.created_at).toLocaleDateString()}
                      </Text>
                    </VStack>

                    <Divider />

                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleExplain(location.id);
                      }}
                      colorScheme="green"
                      variant="outline"
                      size="sm"
                      isLoading={explainLoading}
                      loadingText="Generating..."
                    >
                      Explain Weather
                    </Button>
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        )}

        {/* Weather explanation */}
        {explanation && (
          <Card>
            <CardBody>
              <VStack align="stretch" spacing={4}>
                <Heading size="md">Weather Explanation</Heading>
                
                <VStack align="stretch" spacing={4}>
                  <Box>
                    <Text fontWeight="semibold" color="blue.500" mb={2}>Summary</Text>
                    <Text>{explanation.summary}</Text>
                  </Box>

                  <Box>
                    <Text fontWeight="semibold" color="green.500" mb={2}>Recommended Actions</Text>
                    <VStack align="start" spacing={1}>
                      {explanation.actions.map((action, index) => (
                        <Text key={index} fontSize="sm">• {action}</Text>
                      ))}
                    </VStack>
                  </Box>

                  <Box>
                    <Text fontWeight="semibold" color="orange.500" mb={2}>Weather Driver</Text>
                    <Text>{explanation.driver}</Text>
                  </Box>

                  <Divider />
                  
                  <HStack spacing={4} fontSize="sm" color="gray.500">
                    <Text>Model: {explanation.model}</Text>
                    <Text>•</Text>
                    <Text>Tokens: {explanation.tokens_in} in, {explanation.tokens_out} out</Text>
                  </HStack>
                </VStack>
              </VStack>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
};

export default LocationsView;