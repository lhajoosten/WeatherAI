/**
 * User management types.
 */

export interface UserProfile {
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  time_zone?: string;
  locale?: string;
  theme_preference?: 'light' | 'dark' | 'system';
  created_at?: string;
  updated_at?: string;
}

export interface UserPreferences {
  units_system: 'metric' | 'imperial';
  dashboard_default_location_id?: number;
  show_wind: boolean;
  show_precip: boolean;
  show_humidity: boolean;
  json_settings?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserMeResponse {
  id: number;
  email: string;
  timezone: string;
  created_at: string;
  profile?: UserProfile;
  preferences?: UserPreferences;
}

export interface UserProfileUpdate {
  display_name?: string;
  bio?: string;
  avatar_url?: string;
  time_zone?: string;
  locale?: string;
  theme_preference?: 'light' | 'dark' | 'system';
}

export interface UserPreferencesUpdate {
  units_system?: 'metric' | 'imperial';
  dashboard_default_location_id?: number;
  show_wind?: boolean;
  show_precip?: boolean;
  show_humidity?: boolean;
  json_settings?: string;
}

export interface AvatarUploadResponse {
  avatar_url: string;
  message: string;
}