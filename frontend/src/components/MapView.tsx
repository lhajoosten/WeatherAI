import React, { useEffect, useRef, useState } from 'react';
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
  Tooltip,
  useToast
} from '@chakra-ui/react';
import { MapPin, Layers } from 'react-feather';
import { Location, LocationGroup } from '../types/api';
import { useLocation } from '../context/LocationContext';
import api from '../services/apiClient';

interface MapViewProps {
  onLocationSelect?: (location: Location) => void;
}

const MapView: React.FC<MapViewProps> = ({ onLocationSelect }) => {
  const { locations, selectedLocation, setSelectedLocation } = useLocation();
  const [groups, setGroups] = useState<LocationGroup[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<string>('all');
  const mapRef = useRef<HTMLDivElement>(null);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const toast = useToast();

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const response = await api.get<LocationGroup[]>('/v1/location-groups');
      setGroups(response.data || []); // Defensive: handle undefined response
    } catch (err: any) {
      console.error('Failed to fetch groups:', err);
      // Don't show error toast for groups - it's not critical for map functionality
      setGroups([]); // Ensure groups is always an array
    }
  };

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

  const getLocationColor = (location: Location): string => {
    if (selectedLocation?.id === location.id) return '#3182ce'; // blue
    
    // Color by hemisphere for visual variety
    if (location.lat >= 0) return '#38a169'; // green for northern
    return '#e53e3e'; // red for southern
  };

  const filteredLocations = getFilteredLocations();

  // Calculate map bounds
  const bounds = filteredLocations.length > 0 ? {
    minLat: Math.min(...filteredLocations.map(l => l.lat)),
    maxLat: Math.max(...filteredLocations.map(l => l.lat)),
    minLon: Math.min(...filteredLocations.map(l => l.lon)),
    maxLon: Math.max(...filteredLocations.map(l => l.lon)),
  } : null;

  const centerLat = bounds ? (bounds.minLat + bounds.maxLat) / 2 : 0;
  const centerLon = bounds ? (bounds.minLon + bounds.maxLon) / 2 : 0;

  return (
    <Box bg={bgColor} p={6} borderRadius="lg" border="1px" borderColor={borderColor}>
      <VStack spacing={4} align="stretch">
        {/* Header */}
        <HStack justify="space-between" align="center">
          <HStack spacing={2}>
            <MapPin size={20} color="blue" />
            <Heading size="md">Location Map</Heading>
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

        {/* Map Area - Simplified visualization */}
        <Card>
          <CardBody p={0}>
            <Box
              ref={mapRef}
              height="400px"
              bg={useColorModeValue('blue.50', 'blue.900')}
              position="relative"
              borderRadius="md"
              overflow="hidden"
            >
              {/* Simple coordinate grid background */}
              <Box
                position="absolute"
                top="0"
                left="0"
                right="0"
                bottom="0"
                backgroundImage={`
                  linear-gradient(to right, rgba(0,0,0,0.1) 1px, transparent 1px),
                  linear-gradient(to bottom, rgba(0,0,0,0.1) 1px, transparent 1px)
                `}
                backgroundSize="40px 40px"
              />
              
              {/* Center lines for reference */}
              <Box
                position="absolute"
                top="50%"
                left="0"
                right="0"
                height="1px"
                bg="gray.400"
                opacity="0.5"
              />
              <Box
                position="absolute"
                top="0"
                bottom="0"
                left="50%"
                width="1px"
                bg="gray.400"
                opacity="0.5"
              />
              
              {/* Location markers */}
              {filteredLocations.map((location) => {
                // Defensive: ensure location has required properties
                if (!location || typeof location.lat !== 'number' || typeof location.lon !== 'number') {
                  return null;
                }
                
                // Simple projection: normalize lat/lon to map coordinates
                const x = bounds ? ((location.lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * 100 : 50;
                const y = bounds ? ((bounds.maxLat - location.lat) / (bounds.maxLat - bounds.minLat)) * 100 : 50;
                
                return (
                  <Tooltip
                    key={location.id}
                    label={`${location.name} (${location.lat.toFixed(2)}, ${location.lon.toFixed(2)})`}
                    placement="top"
                  >
                    <Box
                      position="absolute"
                      left={`${Math.max(0, Math.min(95, x))}%`}
                      top={`${Math.max(0, Math.min(95, y))}%`}
                      transform="translate(-50%, -50%)"
                      cursor="pointer"
                      onClick={() => handleLocationClick(location)}
                      _hover={{ transform: "translate(-50%, -50%) scale(1.2)" }}
                      transition="transform 0.2s"
                    >
                      <Box
                        width="12px"
                        height="12px"
                        borderRadius="50%"
                        bg={getLocationColor(location)}
                        border="2px solid white"
                        shadow="sm"
                      />
                      {selectedLocation?.id === location.id && (
                        <Box
                          position="absolute"
                          top="-20px"
                          left="50%"
                          transform="translateX(-50%)"
                          fontSize="xs"
                          bg="blue.500"
                          color="white"
                          px="2"
                          py="1"
                          borderRadius="md"
                          whiteSpace="nowrap"
                          pointerEvents="none"
                        >
                          {location.name}
                        </Box>
                      )}
                    </Box>
                  </Tooltip>
                );
              })}
              
              {/* No locations message */}
              {filteredLocations.length === 0 && (
                <Box
                  position="absolute"
                  top="50%"
                  left="50%"
                  transform="translate(-50%, -50%)"
                  textAlign="center"
                  color="gray.500"
                >
                  <MapPin size={48} style={{ margin: '0 auto 8px' }} />
                  <Text>No locations to display</Text>
                  {selectedGroupId !== 'all' && (
                    <Text fontSize="sm">This group has no locations</Text>
                  )}
                </Box>
              )}
            </Box>
          </CardBody>
        </Card>

        {/* Map Legend */}
        <HStack justify="space-between" fontSize="sm" color="gray.500">
          <HStack spacing={4}>
            <HStack spacing={1}>
              <Box width="8px" height="8px" borderRadius="50%" bg="green.500" />
              <Text>Northern Hemisphere</Text>
            </HStack>
            <HStack spacing={1}>
              <Box width="8px" height="8px" borderRadius="50%" bg="red.500" />
              <Text>Southern Hemisphere</Text>
            </HStack>
            <HStack spacing={1}>
              <Box width="8px" height="8px" borderRadius="50%" bg="blue.500" />
              <Text>Selected Location</Text>
            </HStack>
          </HStack>
          
          {bounds && (
            <Text>
              Center: {centerLat.toFixed(2)}°, {centerLon.toFixed(2)}°
            </Text>
          )}
        </HStack>

        {/* Location List */}
        {filteredLocations.length > 0 && (
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
                        <HStack spacing={2}>
                          <Box
                            width="8px"
                            height="8px"
                            borderRadius="50%"
                            bg={getLocationColor(location)}
                          />
                          <Text fontWeight="medium">{location.name}</Text>
                        </HStack>
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
        )}
      </VStack>
    </Box>
  );
};

export default MapView;