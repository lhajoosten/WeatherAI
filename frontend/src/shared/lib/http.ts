// HTTP client with abort support and error mapping

export interface FetchConfig {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
  retries?: number;
  retryDelay?: number;
}

export class FetchError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: Response,
    public data?: unknown
  ) {
    super(message);
    this.name = 'FetchError';
  }
}

class HttpClient {
  private config: FetchConfig;
  private abortControllers = new Map<string, AbortController>();

  constructor(config: FetchConfig = {}) {
    this.config = {
      timeout: 10000,
      retries: 3,
      retryDelay: 1000,
      ...config,
    };
  }

  private async fetchWithRetry(
    url: string, 
    options: RequestInit & { requestId?: string },
    retryCount = 0
  ): Promise<Response> {
    try {
      const controller = new AbortController();
      const { requestId, ...fetchOptions } = options;
      
      // Store abort controller if requestId provided
      if (requestId) {
        this.abortControllers.set(requestId, controller);
      }

      // Set up timeout
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, this.config.timeout);

      const response = await fetch(url, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...this.config.headers,
          ...fetchOptions.headers,
        },
      });

      clearTimeout(timeoutId);
      
      // Clean up abort controller
      if (requestId) {
        this.abortControllers.delete(requestId);
      }

      if (!response.ok) {
        let errorData: unknown = null;
        try {
          errorData = await response.json();
        } catch {
          // Ignore JSON parsing errors for error responses
        }
        
        throw new FetchError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          response,
          errorData
        );
      }

      return response;
    } catch (error) {
      // Clean up abort controller on error
      if (options.requestId) {
        this.abortControllers.delete(options.requestId);
      }

      if (error instanceof FetchError) {
        throw error;
      }

      // Handle abort/timeout
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new FetchError('Request was aborted or timed out');
      }

      // Handle network errors with retry logic
      if (retryCount < (this.config.retries || 0)) {
        await new Promise(resolve => 
          setTimeout(resolve, this.config.retryDelay! * (retryCount + 1))
        );
        return this.fetchWithRetry(url, options, retryCount + 1);
      }

      throw new FetchError(
        error instanceof Error ? error.message : 'Network error occurred'
      );
    }
  }

  private buildUrl(endpoint: string): string {
    if (endpoint.startsWith('http')) {
      return endpoint;
    }
    
    const baseURL = this.config.baseURL || '';
    return `${baseURL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
  }

  async get<T = unknown>(endpoint: string, options: RequestInit & { requestId?: string } = {}): Promise<T> {
    const response = await this.fetchWithRetry(this.buildUrl(endpoint), {
      method: 'GET',
      ...options,
    });
    
    return response.json();
  }

  async post<T = unknown>(
    endpoint: string, 
    data?: unknown, 
    options: RequestInit & { requestId?: string } = {}
  ): Promise<T> {
    const response = await this.fetchWithRetry(this.buildUrl(endpoint), {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });
    
    return response.json();
  }

  async put<T = unknown>(
    endpoint: string, 
    data?: unknown, 
    options: RequestInit & { requestId?: string } = {}
  ): Promise<T> {
    const response = await this.fetchWithRetry(this.buildUrl(endpoint), {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
    });
    
    return response.json();
  }

  async delete<T = unknown>(endpoint: string, options: RequestInit & { requestId?: string } = {}): Promise<T> {
    const response = await this.fetchWithRetry(this.buildUrl(endpoint), {
      method: 'DELETE',
      ...options,
    });
    
    return response.json();
  }

  // Stream method for server-sent events
  async stream(
    endpoint: string,
    options: RequestInit & { requestId?: string } = {}
  ): Promise<Response> {
    return this.fetchWithRetry(this.buildUrl(endpoint), {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
      ...options,
    });
  }

  // Abort a specific request
  abort(requestId: string): boolean {
    const controller = this.abortControllers.get(requestId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(requestId);
      return true;
    }
    return false;
  }

  // Abort all active requests
  abortAll(): void {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }
}

// Create configured fetch function
export const fetchWithConfig = (config: FetchConfig = {}) => {
  return new HttpClient(config);
};

// Default instance
export const httpClient = new HttpClient();