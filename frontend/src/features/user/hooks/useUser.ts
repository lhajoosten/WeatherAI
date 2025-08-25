/**
 * React Query hooks for user management.
 */

import { useToast } from '@chakra-ui/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import UserApiService from '../services/userApi';
import type {
  UserMeResponse,
  UserProfileUpdate,
  UserPreferencesUpdate,
} from '../types';

// Query keys
export const USER_QUERY_KEYS = {
  me: ['user', 'me'] as const,
  profile: ['user', 'profile'] as const,
  preferences: ['user', 'preferences'] as const,
} as const;

/**
 * Hook to get current user data with profile and preferences.
 */
export const useUserMe = () => {
  return useQuery({
    queryKey: USER_QUERY_KEYS.me,
    queryFn: UserApiService.getMe,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
};

/**
 * Hook to update user profile.
 */
export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (profileData: UserProfileUpdate) => UserApiService.updateProfile(profileData),
    onSuccess: (updatedProfile) => {
      // Update the user data in cache
      queryClient.setQueryData(USER_QUERY_KEYS.me, (oldData: UserMeResponse | undefined) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          profile: updatedProfile,
        };
      });
      
      toast({
        title: 'Profile updated',
        description: 'Your profile has been updated successfully.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error updating profile',
        description: error.response?.data?.detail || 'Failed to update profile.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
  });
};

/**
 * Hook to update user preferences.
 */
export const useUpdatePreferences = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (preferencesData: UserPreferencesUpdate) => UserApiService.updatePreferences(preferencesData),
    onSuccess: (updatedPreferences) => {
      // Update the user data in cache
      queryClient.setQueryData(USER_QUERY_KEYS.me, (oldData: UserMeResponse | undefined) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          preferences: updatedPreferences,
        };
      });
      
      toast({
        title: 'Preferences updated',
        description: 'Your preferences have been updated successfully.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error updating preferences',
        description: error.response?.data?.detail || 'Failed to update preferences.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
  });
};

/**
 * Hook to upload avatar.
 */
export const useUploadAvatar = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (file: File) => UserApiService.uploadAvatar(file),
    onSuccess: (response) => {
      // Update the user profile data in cache
      queryClient.setQueryData(USER_QUERY_KEYS.me, (oldData: UserMeResponse | undefined) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          profile: {
            ...oldData.profile,
            avatar_url: response.avatar_url,
          },
        };
      });
      
      toast({
        title: 'Avatar uploaded',
        description: response.message,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Error uploading avatar',
        description: error.response?.data?.detail || 'Failed to upload avatar.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    },
  });
};