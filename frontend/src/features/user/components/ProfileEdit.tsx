/**
 * ProfileEdit component for editing user profile information.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Avatar,
  Button,
  Card,
  CardHeader,
  CardBody,
  Heading,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
  Alert,
  AlertIcon,
  Skeleton,
  useColorModeValue,
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { Camera, Save, ArrowLeft } from 'react-feather';
import { useUserMe, useUpdateProfile, useUploadAvatar } from '../hooks/useUser';
import { useTheme } from '../../../contexts/ThemeContext';
import type { UserProfileUpdate } from '../types';

export const ProfileEdit: React.FC = () => {
  const navigate = useNavigate();
  const { data: userData, isLoading } = useUserMe();
  const updateProfileMutation = useUpdateProfile();
  const uploadAvatarMutation = useUploadAvatar();
  const { theme, setTheme } = useTheme();

  const [formData, setFormData] = useState<UserProfileUpdate>({
    display_name: '',
    bio: '',
    time_zone: '',
    locale: '',
    theme_preference: 'system',
  });

  const [hasChanges, setHasChanges] = useState(false);

  // Populate form with existing data
  useEffect(() => {
    if (userData?.profile) {
      const profile = userData.profile;
      setFormData({
        display_name: profile.display_name || '',
        bio: profile.bio || '',
        time_zone: profile.time_zone || userData.timezone || '',
        locale: profile.locale || '',
        theme_preference: profile.theme_preference || 'system',
      });
    }
  }, [userData]);

  // Track changes
  useEffect(() => {
    if (userData?.profile) {
      const profile = userData.profile;
      const hasChanged = 
        formData.display_name !== (profile.display_name || '') ||
        formData.bio !== (profile.bio || '') ||
        formData.time_zone !== (profile.time_zone || userData.timezone || '') ||
        formData.locale !== (profile.locale || '') ||
        formData.theme_preference !== (profile.theme_preference || 'system');
      setHasChanges(hasChanged);
    }
  }, [formData, userData]);

  const handleInputChange = (field: keyof UserProfileUpdate, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Filter out empty values
      const updateData: UserProfileUpdate = {};
      Object.entries(formData).forEach(([key, value]) => {
        if (value && value.trim() !== '') {
          updateData[key as keyof UserProfileUpdate] = value;
        }
      });

      await updateProfileMutation.mutateAsync(updateData);
      
      // Update theme if changed
      if (formData.theme_preference && formData.theme_preference !== theme) {
        setTheme(formData.theme_preference);
      }
      
      navigate('/user/profile');
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleAvatarUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      try {
        await uploadAvatarMutation.mutateAsync(file);
      } catch (error) {
        // Error handled by mutation
      }
    }
  };

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  if (isLoading) {
    return (
      <Card>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Skeleton height="24px" width="200px" />
            <Skeleton height="80px" width="80px" borderRadius="full" />
            <Skeleton height="40px" width="100%" />
            <Skeleton height="40px" width="100%" />
            <Skeleton height="80px" width="100%" />
          </VStack>
        </CardBody>
      </Card>
    );
  }

  const profile = userData?.profile;
  const displayName = formData.display_name || 'Anonymous User';
  const avatarUrl = profile?.avatar_url;

  return (
    <Box>
      <Button
        leftIcon={<ArrowLeft size={16} />}
        variant="ghost"
        mb={4}
        onClick={() => navigate('/user/profile')}
      >
        Back to Profile
      </Button>

      <Card bg={bgColor} borderColor={borderColor}>
        <CardHeader>
          <Heading size="md">Edit Profile</Heading>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit}>
            <VStack spacing={6} align="stretch">
              {/* Avatar Section */}
              <Box textAlign="center">
                <VStack spacing={3}>
                  <Avatar
                    size="xl"
                    name={displayName}
                    src={avatarUrl}
                    bg="blue.500"
                  />
                  <Box>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarUpload}
                      style={{ display: 'none' }}
                      id="avatar-upload"
                    />
                    <Button
                      as="label"
                      htmlFor="avatar-upload"
                      leftIcon={<Camera size={16} />}
                      size="sm"
                      variant="outline"
                      cursor="pointer"
                      isLoading={uploadAvatarMutation.isPending}
                    >
                      Change Avatar
                    </Button>
                  </Box>
                </VStack>
              </Box>

              {/* Form Fields */}
              <VStack spacing={4} align="stretch">
                <FormControl>
                  <FormLabel>Display Name</FormLabel>
                  <Input
                    value={formData.display_name}
                    onChange={(e) => handleInputChange('display_name', e.target.value)}
                    placeholder="Enter your display name"
                  />
                </FormControl>

                <FormControl>
                  <FormLabel>Bio</FormLabel>
                  <Textarea
                    value={formData.bio}
                    onChange={(e) => handleInputChange('bio', e.target.value)}
                    placeholder="Tell us about yourself..."
                    rows={3}
                    maxLength={500}
                  />
                  <Text fontSize="sm" color="gray.500" mt={1}>
                    {formData.bio?.length || 0}/500 characters
                  </Text>
                </FormControl>

                <HStack spacing={4}>
                  <FormControl>
                    <FormLabel>Timezone</FormLabel>
                    <Input
                      value={formData.time_zone}
                      onChange={(e) => handleInputChange('time_zone', e.target.value)}
                      placeholder="e.g., America/New_York"
                    />
                  </FormControl>

                  <FormControl>
                    <FormLabel>Language</FormLabel>
                    <Select
                      value={formData.locale}
                      onChange={(e) => handleInputChange('locale', e.target.value)}
                      placeholder="Select language"
                    >
                      <option value="en-US">English (US)</option>
                      <option value="en-GB">English (UK)</option>
                      <option value="es-ES">Español</option>
                      <option value="fr-FR">Français</option>
                      <option value="de-DE">Deutsch</option>
                    </Select>
                  </FormControl>
                </HStack>

                <FormControl>
                  <FormLabel>Theme Preference</FormLabel>
                  <Select
                    value={formData.theme_preference}
                    onChange={(e) => handleInputChange('theme_preference', e.target.value as any)}
                  >
                    <option value="system">System Default</option>
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                  </Select>
                </FormControl>
              </VStack>

              {/* Action Buttons */}
              <HStack justify="space-between" pt={4}>
                <Button
                  variant="outline"
                  onClick={() => navigate('/user/profile')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  colorScheme="blue"
                  leftIcon={<Save size={16} />}
                  isLoading={updateProfileMutation.isPending}
                  isDisabled={!hasChanges}
                >
                  Save Changes
                </Button>
              </HStack>

              {/* Unsaved Changes Warning */}
              {hasChanges && (
                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  You have unsaved changes.
                </Alert>
              )}
            </VStack>
          </form>
        </CardBody>
      </Card>
    </Box>
  );
};