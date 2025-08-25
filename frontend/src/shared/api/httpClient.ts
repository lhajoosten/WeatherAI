import { mapToAppError } from './errors';

const HTTP_TIMEOUT_MS = 10000; // 10 seconds

// Use global RequestInit type that's available in DOM lib

export interface HttpClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface HttpResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

/**
 * Lightweight HTTP client wrapper around fetch API
 * Provides JSON parsing, timeout, error mapping, and instrumentation hooks
 */
export class HttpClient {
  private baseURL: string;
  private timeout: number;
  private defaultHeaders: Record<string, string>;

  constructor(config: HttpClientConfig) {
    this.baseURL = config.baseURL.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = config.timeout || HTTP_TIMEOUT_MS;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
  }

  private async request<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<HttpResponse<T>> {
    const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;
    
    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      // Merge headers
      const headers: Record<string, string> = {
        ...this.defaultHeaders,
        ...(options.headers as Record<string, string> || {}),
      };

      // Add auth token if available
      const token = localStorage.getItem('access_token');
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(fullUrl, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Handle non-2xx status codes
      if (!response.ok) {
        const errorData = await this.parseResponse(response);
        throw {
          response: {
            status: response.status,
            data: errorData,
          },
          message: `HTTP ${response.status}`,
        };
      }

      const data = await this.parseResponse<T>(response);
      
      return {
        data,
        status: response.status,
        headers: response.headers,
      };
    } catch (error: any) {
      clearTimeout(timeoutId);
      
      // Handle timeout
      if (error.name === 'AbortError') {
        throw {
          code: 'ECONNABORTED',
          message: 'Request timeout',
        };
      }

      // Re-throw for error mapping
      throw error;
    }
  }

  private async parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');
    
    if (contentType?.includes('application/json')) {
      return response.json();
    }
    
    // Return text for non-JSON responses
    return response.text() as unknown as T;
  }

  async get<T>(url: string, config?: RequestInit): Promise<T> {
    try {
      const response = await this.request<T>(url, {
        method: 'GET',
        ...config,
      });
      return response.data;
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async post<T>(url: string, data?: any, config?: RequestInit): Promise<T> {
    try {
      const response = await this.request<T>(url, {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
        ...config,
      });
      return response.data;
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async put<T>(url: string, data?: any, config?: RequestInit): Promise<T> {
    try {
      const response = await this.request<T>(url, {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
        ...config,
      });
      return response.data;
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async patch<T>(url: string, data?: any, config?: RequestInit): Promise<T> {
    try {
      const response = await this.request<T>(url, {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
        ...config,
      });
      return response.data;
    } catch (error) {
      throw mapToAppError(error);
    }
  }

  async delete<T>(url: string, config?: RequestInit): Promise<T> {
    try {
      const response = await this.request<T>(url, {
        method: 'DELETE',
        ...config,
      });
      return response.data;
    } catch (error) {
      throw mapToAppError(error);
    }
  }
}