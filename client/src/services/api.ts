import type { QueryResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const API_KEY = import.meta.env.VITE_API_KEY || '';

export class CatalogAPI {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string = API_BASE_URL, apiKey: string = API_KEY) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      'x-api-key': this.apiKey,
    };
  }

  async query(message: string): Promise<QueryResponse> {
    const response = await fetch(
      `${this.baseUrl}/query?q=${encodeURIComponent(message)}`,
      {
        method: 'GET',
        headers: this.getHeaders(),
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Invalid API key. Please check your configuration.');
      }
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  }
}

export const api = new CatalogAPI();
