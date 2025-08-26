/**
 * User management API service.
 */

import { httpClient } from '@/shared/api';
import type {
  UserMeResponse,
  UserProfile,
  UserPreferences,
  UserProfileUpdate,
  UserPreferencesUpdate,
  AvatarUploadResponse,
} from '../types';

export class UserApiService {
  /**
   * Get current user with profile and preferences.
   */
  static async getMe(): Promise<UserMeResponse> {
    const response = await httpClient.get<UserMeResponse>('/v1/user/me');
    return response;
  }

  /**
   * Update user profile.
   */
  static async updateProfile(profileData: UserProfileUpdate): Promise<UserProfile> {
    const response = await httpClient.patch<UserProfile>('/v1/user/profile', profileData);
    return response;
  }

  /**
   * Update user preferences.
   */
  static async updatePreferences(preferencesData: UserPreferencesUpdate): Promise<UserPreferences> {
    const response = await httpClient.patch<UserPreferences>('/v1/user/preferences', preferencesData);
    return response;
  }

  /**
   * Upload user avatar.
   */
  static async uploadAvatar(file: File): Promise<AvatarUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await httpClient.post<AvatarUploadResponse>('/v1/user/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response;
  }
}

export default UserApiService;