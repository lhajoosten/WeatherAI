import { mapToAppError } from './errors';

const HTTP_TIMEOUT_MS = 10000; // 10 seconds

export interface HttpClientConfig {
  baseURL: string; // Should already include /api/v1 for versioned API
  timeout?: number;
  headers?: Record<string, string>;
}

export interface HttpResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

export class HttpClient {
  private baseURL: string;
  private timeout: number;
  private defaultHeaders: Record<string, string>;

  constructor(config: HttpClientConfig) {
    this.baseURL = config.baseURL.replace(/\/$/, '');
    this.timeout = config.timeout || HTTP_TIMEOUT_MS;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
  }

  private buildUrl(url: string): string {
    if (url.startsWith('http')) return url;
    // Ensure leading slash
    const path = url.startsWith('/') ? url : `/${url}`;
    return `${this.baseURL}${path}`.replace(/^(https?:\/\/)(.*)$/i, (_, p, rest) => p + rest.replace(/\/+\/+/g, '/'));
  }

  private async request<T>(url: string, options: RequestInit = {}): Promise<HttpResponse<T>> {
    const fullUrl = this.buildUrl(url);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const headers: Record<string, string> = {
        ...this.defaultHeaders,
        ...(options.headers as Record<string, string> | undefined),
      };

      const token = localStorage.getItem('access_token');
      if (token) headers.Authorization = `Bearer ${token}`;

      const response = await fetch(fullUrl, { ...options, headers, signal: controller.signal });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await this.parseResponse(response);
        throw { response: { status: response.status, data: errorData }, message: `HTTP ${response.status}` };
      }

      const data = await this.parseResponse<T>(response);
      return { data, status: response.status, headers: response.headers };
    } catch (error: unknown) {
      clearTimeout(timeoutId);
      if ((error as { name?: string })?.name === 'AbortError') {
        throw { code: 'ECONNABORTED', message: 'Request timeout' };
      }
      throw error;
    }
  }

  private async parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/json')) return response.json();
    return (response.text() as unknown) as T;
  }

  async get<T>(url: string, config?: RequestInit): Promise<T> {
    try {
      const r = await this.request<T>(url, { method: 'GET', ...config });
      return r.data;
    } catch (e) { throw mapToAppError(e); }
  }
  async post<T>(url: string, data?: unknown, config?: RequestInit): Promise<T> {
    try {
      const r = await this.request<T>(url, { method: 'POST', body: data instanceof FormData ? data : data !== undefined ? JSON.stringify(data) : undefined, ...this.bodyHeaders(data), ...config });
      return r.data;
    } catch (e) { throw mapToAppError(e); }
  }
  async put<T>(url: string, data?: unknown, config?: RequestInit): Promise<T> {
    try {
      const r = await this.request<T>(url, { method: 'PUT', body: data ? JSON.stringify(data) : undefined, ...config });
      return r.data;
    } catch (e) { throw mapToAppError(e); }
  }
  async patch<T>(url: string, data?: unknown, config?: RequestInit): Promise<T> {
    try {
      const r = await this.request<T>(url, { method: 'PATCH', body: data ? JSON.stringify(data) : undefined, ...config });
      return r.data;
    } catch (e) { throw mapToAppError(e); }
  }
  async delete<T>(url: string, config?: RequestInit): Promise<T> {
    try {
      const r = await this.request<T>(url, { method: 'DELETE', ...config });
      return r.data;
    } catch (e) { throw mapToAppError(e); }
  }

  private bodyHeaders(data: unknown): { headers?: Record<string,string> } {
    if (data instanceof FormData) {
      // Let browser set multipart boundary; remove JSON content-type
      const headers = { ...this.defaultHeaders };
      delete headers['Content-Type'];
      return { headers };
    }
    return {};
  }
}