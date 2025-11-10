export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface QueryResponse {
  query: string;
  response: string;
  data?: any;
}

export interface ApiConfig {
  baseUrl: string;
  apiKey: string;
}
