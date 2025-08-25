/**
 * User management API service.
 */

import api from '../../../services/apiClient';
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
    const response = await api.get<UserMeResponse>('/v1/user/me');
    return response.data;
  }

  /**
   * Update user profile.
   */
  static async updateProfile(profileData: UserProfileUpdate): Promise<UserProfile> {
    const response = await api.patch<UserProfile>('/v1/user/profile', profileData);
    return response.data;
  }

  /**
   * Update user preferences.
   */
  static async updatePreferences(preferencesData: UserPreferencesUpdate): Promise<UserPreferences> {
    const response = await api.patch<UserPreferences>('/v1/user/preferences', preferencesData);
    return response.data;
  }

  /**
   * Upload user avatar.
   */
  static async uploadAvatar(file: File): Promise<AvatarUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<AvatarUploadResponse>('/v1/user/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

export default UserApiService;