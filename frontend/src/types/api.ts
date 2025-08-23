// User types
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

// Location types
export interface Location {
  id: number;
  name: string;
  lat: number;
  lon: number;
  timezone?: string;
  created_at: string;
}

export interface LocationCreate {
  name: string;
  lat: number;
  lon: number;
  timezone?: string;
}

// Explain types
export interface ExplainResponse {
  summary: string;
  actions: string[];
  driver: string;
  tokens_in: number;
  tokens_out: number;
  model: string;
}

// Health types
export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  services: Record<string, string>;
}

// Error types
export interface ErrorResponse {
  type: string;
  title: string;
  detail: string;
  status: number;
}