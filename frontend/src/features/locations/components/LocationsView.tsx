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
  Card,
  CardBody,
  Badge,
  useColorModeValue,
  Collapse,
  Divider,
  IconButton,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  useToast,
  Tooltip
} from '@chakra-ui/react';
import { MapPin, Plus, X, Edit, Trash2, Search } from 'react-feather';
import { Location, LocationCreate, LocationUpdate, ExplainResponse, GeoSearchResponse } from '../types/api';
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
  
  // Per-location state instead of global
  const [explanations, setExplanations] = useState<Record<number, ExplainResponse>>({});
  const [loadingLocationId, setLoadingLocationId] = useState<number | null>(null);
  
  // Edit modal state
  const { isOpen: isEditOpen, onOpen: onEditOpen, onClose: onEditClose } = useDisclosure();
  const [editingLocation, setEditingLocation] = useState<Location | null>(null);
  const [editData, setEditData] = useState<LocationUpdate>({});
  
  // Geocoding search state
  const { isOpen: isGeoOpen, onOpen: onGeoOpen, onClose: onGeoClose } = useDisclosure();
  const [geoQuery, setGeoQuery] = useState('');
  const [geoResults, setGeoResults] = useState<GeoSearchResponse | null>(null);
  const [geoLoading, setGeoLoading] = useState(false);

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBgColor = useColorModeValue('white', 'gray.800');
  const toast = useToast();

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
    setLoadingLocationId(locationId);
    setError('');

    try {
      const response = await api.post<ExplainResponse>(`/v1/locations/${locationId}/explain`);
      setExplanations(prev => ({
        ...prev,
        [locationId]: response.data
      }));
    } catch (err: any) {
      setError(err.data?.detail || 'Failed to generate explanation');
    } finally {
      setLoadingLocationId(null);
    }
  };

  const handleEditLocation = (location: Location) => {
    setEditingLocation(location);
    setEditData({
      name: location.name,
      timezone: location.timezone || undefined
    });
    onEditOpen();
  };

  const handleUpdateLocation = async () => {
    if (!editingLocation) return;
    
    try {
      const response = await api.put<Location>(`/v1/locations/${editingLocation.id}`, editData);
      const updatedLocations = locations.map(loc => 
        loc.id === editingLocation.id ? response.data : loc
      );
      setLocations(updatedLocations);
      
      // Update selected location if it was the edited one
      if (selectedLocation?.id === editingLocation.id) {
        setSelectedLocation(response.data);
      }
      
      onEditClose();
      toast({
        title: "Location updated",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (err: any) {
      toast({
        title: "Update failed",
        description: err.data?.detail || 'Failed to update location',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleDeleteLocation = async (locationId: number, locationName: string) => {
    if (!window.confirm(`Are you sure you want to delete "${locationName}"?`)) {
      return;
    }
    
    try {
      await api.delete(`/v1/locations/${locationId}`);
      const updatedLocations = locations.filter(loc => loc.id !== locationId);
      setLocations(updatedLocations);
      
      // Clear selected location if it was deleted
      if (selectedLocation?.id === locationId) {
        setSelectedLocation(updatedLocations.length > 0 ? updatedLocations[0] : null);
      }
      
      // Clear explanation for deleted location
      setExplanations(prev => {
        const newExplanations = { ...prev };
        delete newExplanations[locationId];
        return newExplanations;
      });
      
      toast({
        title: "Location deleted",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    } catch (err: any) {
      toast({
        title: "Delete failed", 
        description: err.data?.detail || 'Failed to delete location',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleGeoSearch = async () => {
    if (geoQuery.trim().length < 2) return;
    
    setGeoLoading(true);
    try {
      const response = await api.get<GeoSearchResponse>(`/v1/geo/search?query=${encodeURIComponent(geoQuery)}`);
      setGeoResults(response.data);
    } catch (err: any) {
      toast({
        title: "Search failed",
        description: err.data?.detail || 'Failed to search locations',
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setGeoLoading(false);
    }
  };

  const handleSelectGeoResult = (result: any) => {
    setNewLocation({
      name: result.display_name,
      lat: result.lat,
      lon: result.lon,
      timezone: result.timezone || 'UTC'
    });
    onGeoClose();
    setShowAddForm(true);
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
          
          <HStack spacing={2}>
            <Button
              leftIcon={<Search size={16} />}
              onClick={onGeoOpen}
              colorScheme="green"
              variant="outline"
            >
              Search
            </Button>
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
                      
                      <HStack spacing={1}>
                        {selectedLocation?.id === location.id && (
                          <Badge colorScheme="blue" variant="solid">
                            Selected
                          </Badge>
                        )}
                        <Tooltip label="Edit location">
                          <IconButton
                            icon={<Edit size={14} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="blue"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEditLocation(location);
                            }}
                            aria-label="Edit location"
                          />
                        </Tooltip>
                        <Tooltip label="Delete location">
                          <IconButton
                            icon={<Trash2 size={14} />}
                            size="sm"
                            variant="ghost"
                            colorScheme="red"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteLocation(location.id, location.name);
                            }}
                            aria-label="Delete location"
                          />
                        </Tooltip>
                      </HStack>
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

                    <VStack spacing={2}>
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleExplain(location.id);
                        }}
                        colorScheme="green"
                        variant="outline"
                        size="sm"
                        width="full"
                        isLoading={loadingLocationId === location.id}
                        loadingText="Generating..."
                      >
                        Explain Weather
                      </Button>
                      
                      {/* Show explanation for this specific location */}
                      {explanations[location.id] && (
                        <Box p={3} bg="gray.50" borderRadius="md" width="full">
                          <Text fontSize="xs" fontWeight="bold" color="green.600" mb={1}>
                            Latest Explanation:
                          </Text>
                          <Text fontSize="xs" noOfLines={2}>
                            {explanations[location.id].summary}
                          </Text>
                        </Box>
                      )}
                    </VStack>
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        )}
        
        {/* Edit Location Modal */}
        <Modal isOpen={isEditOpen} onClose={onEditClose}>
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Edit Location</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4}>
                <FormControl>
                  <FormLabel>Name</FormLabel>
                  <Input
                    value={editData.name || ''}
                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                    placeholder="Location name"
                  />
                </FormControl>
                <FormControl>
                  <FormLabel>Timezone</FormLabel>
                  <Select
                    value={editData.timezone || ''}
                    onChange={(e) => setEditData({ ...editData, timezone: e.target.value })}
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
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button variant="ghost" mr={3} onClick={onEditClose}>
                Cancel
              </Button>
              <Button colorScheme="blue" onClick={handleUpdateLocation}>
                Update
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

        {/* Geocoding Search Modal */}
        <Modal isOpen={isGeoOpen} onClose={onGeoClose} size="lg">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>Search Locations</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <VStack spacing={4}>
                <HStack width="full">
                  <Input
                    value={geoQuery}
                    onChange={(e) => setGeoQuery(e.target.value)}
                    placeholder="Search for a city, state, or country..."
                    onKeyPress={(e) => e.key === 'Enter' && handleGeoSearch()}
                  />
                  <Button
                    onClick={handleGeoSearch}
                    colorScheme="blue"
                    isLoading={geoLoading}
                    loadingText="Searching..."
                  >
                    Search
                  </Button>
                </HStack>
                
                {geoResults && (
                  <VStack align="stretch" width="full" maxH="400px" overflowY="auto">
                    <Text fontWeight="semibold">
                      Found {geoResults.count} results for "{geoResults.query}":
                    </Text>
                    {geoResults.results.map((result, index) => (
                      <Card
                        key={index}
                        cursor="pointer"
                        _hover={{ bg: "blue.50" }}
                        onClick={() => handleSelectGeoResult(result)}
                      >
                        <CardBody py={3}>
                          <VStack align="start" spacing={1}>
                            <Text fontWeight="semibold">{result.display_name}</Text>
                            <Text fontSize="sm" color="gray.500">
                              {result.lat.toFixed(4)}, {result.lon.toFixed(4)} • {result.timezone}
                            </Text>
                          </VStack>
                        </CardBody>
                      </Card>
                    ))}
                  </VStack>
                )}
              </VStack>
            </ModalBody>
            <ModalFooter>
              <Button onClick={onGeoClose}>Close</Button>
            </ModalFooter>
          </ModalContent>
        </Modal>
      </VStack>
    </Box>
  );
};

export default LocationsView;