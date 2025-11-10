import { createSignal } from 'solid-js';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput(props: ChatInputProps) {
  const [input, setInput] = createSignal('');

  const handleSubmit = (e: Event) => {
    e.preventDefault();
    const message = input().trim();
    if (message && !props.disabled) {
      props.onSend(message);
      setInput('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form class="chat-input-form" onSubmit={handleSubmit}>
      <textarea
        class="chat-input"
        value={input()}
        onInput={(e) => setInput(e.currentTarget.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about datasets, keywords, or schema..."
        disabled={props.disabled}
        rows={1}
      />
      <button
        type="submit"
        class="chat-submit"
        disabled={props.disabled || !input().trim()}
      >
        Send
      </button>
    </form>
  );
}
