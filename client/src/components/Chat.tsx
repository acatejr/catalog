import { createSignal, onMount, createEffect } from 'solid-js';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { api } from '../services/api';
import type { Message } from '../types';

export function Chat() {
  const [messages, setMessages] = createSignal<Message[]>([]);
  const [isLoading, setIsLoading] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);
  const [isConnected, setIsConnected] = createSignal(false);

  let messagesEndRef: HTMLDivElement | undefined;

  onMount(async () => {
    // Check API connection on mount
    try {
      await api.healthCheck();
      setIsConnected(true);
      addSystemMessage('Connected to Catalog API. Ask me anything about the catalog!');
    } catch (err) {
      setIsConnected(false);
      setError('Failed to connect to API. Please check your configuration.');
    }
  });

  // Auto-scroll to bottom when new messages arrive
  createEffect(() => {
    if (messages().length > 0 && messagesEndRef) {
      messagesEndRef.scrollIntoView({ behavior: 'smooth' });
    }
  });

  const addSystemMessage = (content: string) => {
    const message: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, message]);
  };

  const handleSendMessage = async (content: string) => {
    if (!isConnected()) {
      setError('Not connected to API');
      return;
    }

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.query(content);

      // Add assistant response
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      addSystemMessage(`Error: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div class="chat-container">
      <div class="chat-header">
        <h1>Catalog Chatbot</h1>
        <div class="connection-status">
          <span class={`status-indicator ${isConnected() ? 'connected' : 'disconnected'}`} />
          {isConnected() ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      <div class="chat-messages">
        <MessageList messages={messages()} />
        <div ref={messagesEndRef} />
      </div>

      {error() && (
        <div class="error-banner">
          {error()}
        </div>
      )}

      <div class="chat-input-container">
        <ChatInput
          onSend={handleSendMessage}
          disabled={isLoading() || !isConnected()}
        />
        {isLoading() && <div class="loading-indicator">Thinking...</div>}
      </div>
    </div>
  );
}
