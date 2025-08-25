/**
 * PreferencesForm component for managing user preferences.
 */

import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Card,
  CardHeader,
  CardBody,
  Heading,
  FormControl,
  FormLabel,
  Select,
  Switch,
  Alert,
  AlertIcon,
  Skeleton,
  Divider,
  useColorModeValue,
} from '@chakra-ui/react';
import React, { useState, useEffect } from 'react';
import { Save, Thermometer, Wind, CloudRain, Droplet } from 'react-feather';

import { useUserMe, useUpdatePreferences } from '../hooks/useUser';
import type { UserPreferencesUpdate } from '../types';

export const PreferencesForm: React.FC = () => {
  const { data: userData, isLoading } = useUserMe();
  const updatePreferencesMutation = useUpdatePreferences();

  const [formData, setFormData] = useState<UserPreferencesUpdate>({
    units_system: 'metric',
    show_wind: true,
    show_precip: true,
    show_humidity: true,
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Populate form with existing data
  useEffect(() => {
    if (userData?.preferences) {
      const prefs = userData.preferences;
      setFormData({
        units_system: prefs.units_system,
        dashboard_default_location_id: prefs.dashboard_default_location_id,
        show_wind: prefs.show_wind,
        show_precip: prefs.show_precip,
        show_humidity: prefs.show_humidity,
      });
    }
  }, [userData]);

  // Track changes
  useEffect(() => {
    if (userData?.preferences) {
      const prefs = userData.preferences;
      const hasChanged = 
        formData.units_system !== prefs.units_system ||
        formData.dashboard_default_location_id !== prefs.dashboard_default_location_id ||
        formData.show_wind !== prefs.show_wind ||
        formData.show_precip !== prefs.show_precip ||
        formData.show_humidity !== prefs.show_humidity;
      setHasChanges(hasChanged);
    }
  }, [formData, userData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await updatePreferencesMutation.mutateAsync(formData);
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleSwitchChange = (field: keyof UserPreferencesUpdate, value: boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSelectChange = (field: keyof UserPreferencesUpdate, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  if (isLoading) {
    return (
      <Card>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Skeleton height="24px" width="200px" />
            <Skeleton height="40px" width="100%" />
            <Skeleton height="40px" width="100%" />
            <Skeleton height="40px" width="100%" />
            <Skeleton height="40px" width="100%" />
          </VStack>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card bg={bgColor} borderColor={borderColor}>
      <CardHeader>
        <Heading size="md">Weather Preferences</Heading>
      </CardHeader>
      <CardBody>
        <form onSubmit={handleSubmit}>
          <VStack spacing={6} align="stretch">
            {/* Units System */}
            <Box>
              <Heading size="sm" mb={4} color="gray.700">
                Units & Display
              </Heading>
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>
                    <HStack>
                      <Thermometer size={16} />
                      <Text>Units System</Text>
                    </HStack>
                  </FormLabel>
                  <Select
                    value={formData.units_system}
                    onChange={(e) => handleSelectChange('units_system', e.target.value as 'metric' | 'imperial')}
                  >
                    <option value="metric">Metric (°C, km/h, mm)</option>
                    <option value="imperial">Imperial (°F, mph, in)</option>
                  </Select>
                  <Text fontSize="sm" color="gray.500" mt={1}>
                    Choose your preferred units for temperature, wind speed, and precipitation.
                  </Text>
                </FormControl>
              </VStack>
            </Box>

            <Divider />

            {/* Weather Elements */}
            <Box>
              <Heading size="sm" mb={4} color="gray.700">
                Weather Elements
              </Heading>
              <Text fontSize="sm" color="gray.500" mb={4}>
                Choose which weather information to display on your dashboard.
              </Text>
              
              <VStack spacing={4} align="stretch">
                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel mb={0} flex={1}>
                    <HStack>
                      <Wind size={16} />
                      <VStack align="start" spacing={0}>
                        <Text>Wind Information</Text>
                        <Text fontSize="sm" color="gray.500">
                          Show wind speed and direction
                        </Text>
                      </VStack>
                    </HStack>
                  </FormLabel>
                  <Switch
                    isChecked={formData.show_wind}
                    onChange={(e) => handleSwitchChange('show_wind', e.target.checked)}
                    colorScheme="blue"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel mb={0} flex={1}>
                    <HStack>
                      <CloudRain size={16} />
                      <VStack align="start" spacing={0}>
                        <Text>Precipitation</Text>
                        <Text fontSize="sm" color="gray.500">
                          Show rainfall and precipitation data
                        </Text>
                      </VStack>
                    </HStack>
                  </FormLabel>
                  <Switch
                    isChecked={formData.show_precip}
                    onChange={(e) => handleSwitchChange('show_precip', e.target.checked)}
                    colorScheme="blue"
                  />
                </FormControl>

                <FormControl display="flex" alignItems="center" justifyContent="space-between">
                  <FormLabel mb={0} flex={1}>
                    <HStack>
                      <Droplet size={16} />
                      <VStack align="start" spacing={0}>
                        <Text>Humidity</Text>
                        <Text fontSize="sm" color="gray.500">
                          Show relative humidity percentage
                        </Text>
                      </VStack>
                    </HStack>
                  </FormLabel>
                  <Switch
                    isChecked={formData.show_humidity}
                    onChange={(e) => handleSwitchChange('show_humidity', e.target.checked)}
                    colorScheme="blue"
                  />
                </FormControl>
              </VStack>
            </Box>

            {/* Action Buttons */}
            <HStack justify="flex-end" pt={4}>
              <Button
                type="submit"
                colorScheme="blue"
                leftIcon={<Save size={16} />}
                isLoading={updatePreferencesMutation.isPending}
                isDisabled={!hasChanges}
              >
                Save Preferences
              </Button>
            </HStack>

            {/* Unsaved Changes Warning */}
            {hasChanges && (
              <Alert status="info" borderRadius="md">
                <AlertIcon />
                You have unsaved changes to your preferences.
              </Alert>
            )}

            {/* Current Settings Summary */}
            <Box p={4} bg="gray.50" borderRadius="md" border="1px solid" borderColor="gray.200">
              <Heading size="xs" mb={2} color="gray.600">
                Current Settings Summary
              </Heading>
              <VStack spacing={1} align="start" fontSize="sm" color="gray.600">
                <Text>• Units: {formData.units_system === 'metric' ? 'Metric' : 'Imperial'}</Text>
                <Text>• Wind: {formData.show_wind ? 'Shown' : 'Hidden'}</Text>
                <Text>• Precipitation: {formData.show_precip ? 'Shown' : 'Hidden'}</Text>
                <Text>• Humidity: {formData.show_humidity ? 'Shown' : 'Hidden'}</Text>
              </VStack>
            </Box>
          </VStack>
        </form>
      </CardBody>
    </Card>
  );
};