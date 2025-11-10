import { For } from 'solid-js';
import type { Message } from '../types';

interface MessageListProps {
  messages: Message[];
}

export function MessageList(props: MessageListProps) {
  return (
    <div class="message-list">
      <For each={props.messages}>
        {(message) => (
          <div class={`message message-${message.role}`}>
            <div class="message-role">
              {message.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div class="message-content">{message.content}</div>
            <div class="message-timestamp">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        )}
      </For>
    </div>
  );
}
