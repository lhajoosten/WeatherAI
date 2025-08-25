import React, { useEffect, useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Card,
  CardBody,
  Badge,
  useColorModeValue,
  Select,
  useToast
} from '@chakra-ui/react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { LatLngExpression } from 'leaflet';
import { MapPin, Layers } from 'react-feather';
import { Location, LocationGroup } from '../types/api';
import { useLocation } from '../context/LocationContext';
import api from '../services/apiClient';

// Import Leaflet CSS
import 'leaflet/dist/leaflet.css';

// Fix for default marker icons in react-leaflet
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [0, -41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface MapViewProps {
  onLocationSelect?: (location: Location) => void;
}

const MapView: React.FC<MapViewProps> = ({ onLocationSelect }) => {
  const { locations, selectedLocation, setSelectedLocation } = useLocation();
  const [groups, setGroups] = useState<LocationGroup[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<string>('all');
  const [isLoadingGroups, setIsLoadingGroups] = useState(false);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const toast = useToast();

  useEffect(() => {
    let isMounted = true;  // Guard against duplicate fetches in strict mode
    
    const loadGroups = async () => {
      if (isLoadingGroups) return;  // Prevent duplicate requests
      
      try {
        setIsLoadingGroups(true);
        const response = await api.get('/v1/location-groups');
        if (isMounted) {
          setGroups(response.data || []);
        }
      } catch (error) {
        console.error('Failed to load location groups:', error);
      } finally {
        if (isMounted) {
          setIsLoadingGroups(false);
        }
      }
    };

    loadGroups();
    
    return () => {
      isMounted = false;
    };
  }, [isLoadingGroups]);

  const getFilteredLocations = (): Location[] => {
    // Defensive programming: ensure locations array exists
    if (!locations || !Array.isArray(locations)) {
      return [];
    }
    
    if (selectedGroupId === 'all') {
      return locations;
    }
    
    const group = groups.find(g => g.id.toString() === selectedGroupId);
    return group?.members || [];
  };

  const handleLocationClick = (location: Location) => {
    setSelectedLocation(location);
    onLocationSelect?.(location);
    
    toast({
      title: "Location selected",
      description: `Selected ${location.name}`,
      status: "info",
      duration: 2000,
      isClosable: true,
    });
  };

  const filteredLocations = getFilteredLocations();

  // Calculate map bounds and center
  const bounds = filteredLocations.length > 0 ? {
    minLat: Math.min(...filteredLocations.map(l => l.lat)),
    maxLat: Math.max(...filteredLocations.map(l => l.lat)),
    minLon: Math.min(...filteredLocations.map(l => l.lon)),
    maxLon: Math.max(...filteredLocations.map(l => l.lon)),
  } : null;

  const centerLat = bounds ? (bounds.minLat + bounds.maxLat) / 2 : 40.7128;  // Default to NYC
  const centerLon = bounds ? (bounds.minLon + bounds.maxLon) / 2 : -74.0060;

  return (
    <Box bg={bgColor} p={6} borderRadius="lg" border="1px" borderColor={borderColor}>
      <VStack spacing={4} align="stretch">
        {/* Header */}
        <HStack justify="space-between" align="center">
          <HStack spacing={2}>
            <MapPin size={20} color="blue" />
            <Heading size="md">Location Map</Heading>
            <Badge colorScheme="blue">{filteredLocations.length} locations</Badge>
          </HStack>
          
          <HStack spacing={2}>
            <Layers size={16} />
            <Select
              value={selectedGroupId}
              onChange={(e) => setSelectedGroupId(e.target.value)}
              size="sm"
              width="200px"
            >
              <option value="all">All Locations ({locations.length})</option>
              {groups.map(group => (
                <option key={group.id} value={group.id.toString()}>
                  {group.name} ({group.members.length})
                </option>
              ))}
            </Select>
          </HStack>
        </HStack>

        {/* Leaflet Map */}
        <Card>
          <CardBody p={0}>
            <Box height="400px" borderRadius="md" overflow="hidden">
              {filteredLocations.length > 0 ? (
                <MapContainer
                  center={[centerLat, centerLon] as LatLngExpression}
                  zoom={filteredLocations.length === 1 ? 10 : 6}
                  style={{ height: '100%', width: '100%' }}
                  scrollWheelZoom={true}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  
                  {filteredLocations.map((location) => {
                    // Ensure location has valid coordinates
                    if (!location || typeof location.lat !== 'number' || typeof location.lon !== 'number') {
                      return null;
                    }
                    
                    return (
                      <Marker
                        key={location.id}
                        position={[location.lat, location.lon] as LatLngExpression}
                        eventHandlers={{
                          click: () => handleLocationClick(location),
                        }}
                      >
                        <Popup>
                          <VStack spacing={2} align="start">
                            <Text fontWeight="bold">{location.name}</Text>
                            <Text fontSize="sm">
                              Lat: {location.lat.toFixed(4)}, Lon: {location.lon.toFixed(4)}
                            </Text>
                            {location.timezone && (
                              <Text fontSize="sm">Timezone: {location.timezone}</Text>
                            )}
                            {selectedLocation?.id === location.id && (
                              <Badge colorScheme="blue" size="sm">Selected</Badge>
                            )}
                          </VStack>
                        </Popup>
                      </Marker>
                    );
                  })}
                </MapContainer>
              ) : (
                <Box 
                  height="400px" 
                  display="flex" 
                  alignItems="center" 
                  justifyContent="center"
                  bg={useColorModeValue('gray.50', 'gray.700')}
                >
                  <VStack spacing={2}>
                    <MapPin size={48} color="gray" />
                    <Text color="gray.500">No locations to display</Text>
                    <Text fontSize="sm" color="gray.400">
                      Add some locations to see them on the map
                    </Text>
                  </VStack>
                </Box>
              )}
            </Box>
          </CardBody>
        </Card>

        {/* Location Details */}
        {selectedLocation && (
          <Card>
            <CardBody>
              <VStack align="start" spacing={2}>
                <HStack>
                  <MapPin size={16} />
                  <Text fontWeight="bold">Selected Location</Text>
                </HStack>
                <Text>{selectedLocation.name}</Text>
                <Text fontSize="sm" color="gray.600">
                  {selectedLocation.lat.toFixed(4)}, {selectedLocation.lon.toFixed(4)}
                </Text>
                {selectedLocation.timezone && (
                  <Text fontSize="sm" color="gray.600">
                    {selectedLocation.timezone}
                  </Text>
                )}
              </VStack>
            </CardBody>
          </Card>
        )}

        {/* Location List for mobile/backup */}
        {filteredLocations.length > 0 && (
          <Card>
            <CardBody>
              <VStack align="stretch" spacing={2}>
                <Text fontSize="sm" fontWeight="semibold" color="gray.600">
                  Locations ({filteredLocations.length}):
                </Text>
                <Box maxHeight="150px" overflowY="auto">
                  <VStack spacing={1}>
                    {filteredLocations.map((location) => (
                      <Card
                        key={location.id}
                        width="full"
                        size="sm"
                        cursor="pointer"
                        onClick={() => handleLocationClick(location)}
                        bg={selectedLocation?.id === location.id ? "blue.50" : "transparent"}
                        _hover={{ bg: "gray.50" }}
                        transition="background 0.2s"
                      >
                        <CardBody py={2}>
                          <HStack justify="space-between">
                            <Text fontWeight="medium">{location.name}</Text>
                            <HStack spacing={2}>
                              <Text fontSize="xs" color="gray.500">
                                {location.lat.toFixed(2)}°, {location.lon.toFixed(2)}°
                              </Text>
                              {selectedLocation?.id === location.id && (
                                <Badge colorScheme="blue" size="sm">Selected</Badge>
                              )}
                            </HStack>
                          </HStack>
                        </CardBody>
                      </Card>
                    ))}
                  </VStack>
                </Box>
              </VStack>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Box>
  );
};

export default MapView;