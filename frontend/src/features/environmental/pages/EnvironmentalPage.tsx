import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Select,
  SimpleGrid,
  Spinner,
  Alert,
  AlertIcon,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Icon,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
} from '@chakra-ui/react';
import { subDays, format } from 'date-fns';
import { Wind, Sun, Moon, Droplet, AlertTriangle } from 'react-feather';
import { useLocation } from '@/features/locations/context/LocationContext';
import { useAirQuality, useAstronomy } from '../hooks/useEnvironmental';

const EnvironmentalPage: React.FC = () => {
  const { selectedLocation, locations } = useLocation();
  const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '14d' | '30d'>('7d');
  
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBgColor = useColorModeValue('white', 'gray.800');
  
  // Date ranges for data fetching
  const endDate = new Date();
  const startDate = selectedPeriod === '7d' ? subDays(endDate, 7) :
                   selectedPeriod === '14d' ? subDays(endDate, 14) :
                   subDays(endDate, 30);
  
  // Data fetching hooks
  const {
    data: airQuality,
    isLoading: airQualityLoading,
    error: airQualityError
  } = useAirQuality(selectedLocation?.id || 0, startDate, endDate, !!selectedLocation);
  
  const {
    data: astronomy,
    isLoading: astronomyLoading,
    error: astronomyError
  } = useAstronomy(selectedLocation?.id || 0, startDate, endDate, !!selectedLocation);

  const isLoading = airQualityLoading || astronomyLoading;
  const hasError = airQualityError || astronomyError;

  // Air quality metrics helpers
  const getAQILevel = (pm25?: number) => {
    if (!pm25) return { level: 'Unknown', color: 'gray' };
    if (pm25 <= 12) return { level: 'Good', color: 'green' };
    if (pm25 <= 35.4) return { level: 'Moderate', color: 'yellow' };
    if (pm25 <= 55.4) return { level: 'Unhealthy for Sensitive', color: 'orange' };
    if (pm25 <= 150.4) return { level: 'Unhealthy', color: 'red' };
    return { level: 'Very Unhealthy', color: 'purple' };
  };

  const getPollenLevel = (count?: number) => {
    if (!count) return { level: 'Unknown', color: 'gray' };
    if (count <= 2) return { level: 'Low', color: 'green' };
    if (count <= 4) return { level: 'Moderate', color: 'yellow' };
    return { level: 'High', color: 'red' };
  };

  // Get latest air quality data
  const latestAirQuality = airQuality?.data?.[0];
  const latestAstronomy = astronomy?.data?.[0];

  if (!selectedLocation) {
    return (
      <Box p={8} textAlign="center">
        <Heading size="lg" mb={4}>Environmental Data</Heading>
        <Text color="gray.500">
          {locations.length === 0 
            ? "No locations available. Add a location first."
            : "Select a location to view environmental data."
          }
        </Text>
      </Box>
    );
  }

  return (
    <Box bg={bgColor} minH="100vh" p={6}>
      <VStack spacing={6} align="stretch" maxW="1200px" mx="auto">
        {/* Header */}
        <Box textAlign="center">
          <Heading size="xl" mb={2} color="green.500">
            Environmental Data
          </Heading>
          <Text color="gray.500" fontSize="lg">
            Air quality, astronomy, and environmental insights for {selectedLocation.name}
          </Text>
        </Box>

        {/* Controls */}
        <Box bg={cardBgColor} p={4} borderRadius="lg" shadow="sm">
          <HStack justify="space-between" align="center">
            <Text fontWeight="semibold">Data Period</Text>
            <Select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value as '7d' | '14d' | '30d')}
              width="auto"
              size="sm"
            >
              <option value="7d">Last 7 days</option>
              <option value="14d">Last 14 days</option>
              <option value="30d">Last 30 days</option>
            </Select>
          </HStack>
          <Text fontSize="sm" color="gray.500" mt={2}>
            Period: {format(startDate, 'MMM dd, yyyy')} - {format(endDate, 'MMM dd, yyyy')}
          </Text>
        </Box>

        {/* Error display */}
        {hasError && (
          <Alert status="error" borderRadius="lg">
            <AlertIcon />
            Failed to load environmental data. This could be because no data is available for the selected location and period.
          </Alert>
        )}

        {/* Loading indicator */}
        {isLoading && (
          <Box textAlign="center" py={8}>
            <Spinner size="lg" color="green.500" />
            <Text mt={4} color="gray.500">Loading environmental data...</Text>
          </Box>
        )}

        {/* Content */}
        {!isLoading && (
          <Tabs isFitted variant="enclosed" colorScheme="green">
            <TabList>
              <Tab>
                <HStack spacing={2}>
                  <Icon as={Wind} size={16} />
                  <Text>Air Quality</Text>
                  {latestAirQuality && (
                    <Badge colorScheme={getAQILevel(latestAirQuality.pm2_5).color} variant="subtle">
                      {getAQILevel(latestAirQuality.pm2_5).level}
                    </Badge>
                  )}
                </HStack>
              </Tab>
              <Tab>
                <HStack spacing={2}>
                  <Icon as={Sun} size={16} />
                  <Text>Astronomy</Text>
                  {latestAstronomy && (
                    <Badge colorScheme="yellow" variant="subtle">
                      {latestAstronomy.moon_phase || 'N/A'}
                    </Badge>
                  )}
                </HStack>
              </Tab>
            </TabList>

            <TabPanels>
              {/* Air Quality Tab */}
              <TabPanel p={6}>
                {airQuality?.data && airQuality.data.length > 0 ? (
                  <VStack spacing={6} align="stretch">
                    {/* Current Conditions */}
                    {latestAirQuality && (
                      <Card>
                        <CardBody>
                          <VStack align="stretch" spacing={4}>
                            <HStack justify="space-between">
                              <Text fontSize="lg" fontWeight="semibold">Current Air Quality</Text>
                              <Text fontSize="sm" color="gray.500">
                                {new Date(latestAirQuality.observed_at).toLocaleString()}
                              </Text>
                            </HStack>
                            
                            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
                              <Stat>
                                <StatLabel>PM2.5</StatLabel>
                                <StatNumber>{latestAirQuality.pm2_5?.toFixed(1) || 'N/A'}</StatNumber>
                                <StatHelpText>μg/m³</StatHelpText>
                              </Stat>
                              
                              <Stat>
                                <StatLabel>PM10</StatLabel>
                                <StatNumber>{latestAirQuality.pm10?.toFixed(1) || 'N/A'}</StatNumber>
                                <StatHelpText>μg/m³</StatHelpText>
                              </Stat>
                              
                              <Stat>
                                <StatLabel>Ozone</StatLabel>
                                <StatNumber>{latestAirQuality.ozone?.toFixed(1) || 'N/A'}</StatNumber>
                                <StatHelpText>ppb</StatHelpText>
                              </Stat>
                              
                              <Stat>
                                <StatLabel>NO2</StatLabel>
                                <StatNumber>{latestAirQuality.no2?.toFixed(1) || 'N/A'}</StatNumber>
                                <StatHelpText>ppb</StatHelpText>
                              </Stat>
                            </SimpleGrid>

                            {/* Pollen Data */}
                            {(latestAirQuality.pollen_tree || latestAirQuality.pollen_grass || latestAirQuality.pollen_weed) && (
                              <>
                                <Text fontWeight="semibold" mt={4}>Pollen Levels</Text>
                                <SimpleGrid columns={3} spacing={4}>
                                  <Box textAlign="center">
                                    <Text fontSize="sm" color="gray.500">Tree</Text>
                                    <Badge colorScheme={getPollenLevel(latestAirQuality.pollen_tree).color}>
                                      {getPollenLevel(latestAirQuality.pollen_tree).level}
                                    </Badge>
                                  </Box>
                                  <Box textAlign="center">
                                    <Text fontSize="sm" color="gray.500">Grass</Text>
                                    <Badge colorScheme={getPollenLevel(latestAirQuality.pollen_grass).color}>
                                      {getPollenLevel(latestAirQuality.pollen_grass).level}
                                    </Badge>
                                  </Box>
                                  <Box textAlign="center">
                                    <Text fontSize="sm" color="gray.500">Weed</Text>
                                    <Badge colorScheme={getPollenLevel(latestAirQuality.pollen_weed).color}>
                                      {getPollenLevel(latestAirQuality.pollen_weed).level}
                                    </Badge>
                                  </Box>
                                </SimpleGrid>
                              </>
                            )}
                          </VStack>
                        </CardBody>
                      </Card>
                    )}

                    {/* Data Summary */}
                    <Card>
                      <CardBody>
                        <Text fontWeight="semibold" mb={3}>Data Summary</Text>
                        <Text fontSize="sm" color="gray.600">
                          Found {airQuality.count} air quality records from {airQuality.start} to {airQuality.end}
                        </Text>
                      </CardBody>
                    </Card>
                  </VStack>
                ) : (
                  <Box textAlign="center" py={12}>
                    <Icon as={AlertTriangle} size={48} color="gray.400" mb={4} />
                    <Text fontSize="lg" color="gray.500">No air quality data available</Text>
                    <Text color="gray.400">
                      No air quality data found for the selected period.
                    </Text>
                  </Box>
                )}
              </TabPanel>

              {/* Astronomy Tab */}
              <TabPanel p={6}>
                {astronomy?.data && astronomy.data.length > 0 ? (
                  <VStack spacing={6} align="stretch">
                    {/* Today's Astronomy */}
                    {latestAstronomy && (
                      <Card>
                        <CardBody>
                          <VStack align="stretch" spacing={4}>
                            <HStack justify="space-between">
                              <Text fontSize="lg" fontWeight="semibold">Today's Astronomy</Text>
                              <Text fontSize="sm" color="gray.500">
                                {new Date(latestAstronomy.date).toLocaleDateString()}
                              </Text>
                            </HStack>
                            
                            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={6}>
                              <VStack spacing={2}>
                                <Icon as={Sun} size={24} color="orange.400" />
                                <Text fontSize="sm" color="gray.500">Sunrise</Text>
                                <Text fontWeight="semibold">
                                  {latestAstronomy.sunrise_utc 
                                    ? new Date(latestAstronomy.sunrise_utc).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                                    : 'N/A'
                                  }
                                </Text>
                              </VStack>
                              
                              <VStack spacing={2}>
                                <Icon as={Moon} size={24} color="blue.400" />
                                <Text fontSize="sm" color="gray.500">Sunset</Text>
                                <Text fontWeight="semibold">
                                  {latestAstronomy.sunset_utc 
                                    ? new Date(latestAstronomy.sunset_utc).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                                    : 'N/A'
                                  }
                                </Text>
                              </VStack>
                              
                              <VStack spacing={2}>
                                <Icon as={Droplet} size={24} color="purple.400" />
                                <Text fontSize="sm" color="gray.500">Daylight</Text>
                                <Text fontWeight="semibold">
                                  {latestAstronomy.daylight_minutes 
                                    ? `${Math.floor(latestAstronomy.daylight_minutes / 60)}h ${latestAstronomy.daylight_minutes % 60}m`
                                    : 'N/A'
                                  }
                                </Text>
                              </VStack>
                              
                              <VStack spacing={2}>
                                <Icon as={Moon} size={24} color="gray.400" />
                                <Text fontSize="sm" color="gray.500">Moon Phase</Text>
                                <Text fontWeight="semibold">
                                  {latestAstronomy.moon_phase || 'N/A'}
                                </Text>
                              </VStack>
                            </SimpleGrid>
                          </VStack>
                        </CardBody>
                      </Card>
                    )}

                    {/* Data Summary */}
                    <Card>
                      <CardBody>
                        <Text fontWeight="semibold" mb={3}>Data Summary</Text>
                        <Text fontSize="sm" color="gray.600">
                          Found {astronomy.count} astronomy records from {astronomy.start} to {astronomy.end}
                        </Text>
                      </CardBody>
                    </Card>
                  </VStack>
                ) : (
                  <Box textAlign="center" py={12}>
                    <Icon as={Sun} size={48} color="gray.400" mb={4} />
                    <Text fontSize="lg" color="gray.500">No astronomy data available</Text>
                    <Text color="gray.400">
                      No astronomy data found for the selected period.
                    </Text>
                  </Box>
                )}
              </TabPanel>
            </TabPanels>
          </Tabs>
        )}
      </VStack>
    </Box>
  );
};

export default EnvironmentalPage;