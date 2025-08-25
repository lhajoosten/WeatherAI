// Placeholder API types - will be populated during migration from existing types/api.ts

// User types (placeholder structure)
export interface User {
  id: number;
  email: string;
  timezone: string;
  created_at: string;
}

export interface UserCreate {
  email: string;
  password: string;
  timezone?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Location types (placeholder structure)
export interface Location {
  id: number;
  name: string;
  lat: number;
  lon: number;
  timezone: string | null;
  created_at: string;
}

// Health check types
export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  services: Record<string, string>;
}

// Error types
export interface ErrorResponse {
  detail: string;
  code?: string;
  message?: string;
}

// Note: Full API types will be migrated from existing types/api.ts in PR2/PR3