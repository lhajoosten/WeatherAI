import { HttpClient } from './httpClient';

import { getConfig } from '@/shared/config';

// Create a singleton HTTP client instance
let clientInstance: HttpClient | null = null;

export function getHttpClient(): HttpClient {
  if (!clientInstance) {
    const config = getConfig();
    clientInstance = new HttpClient({
      baseURL: config.PUBLIC_API_BASE_URL,
    });
  }
  return clientInstance;
}

// Export the client instance
export const httpClient = getHttpClient();