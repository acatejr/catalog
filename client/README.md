# Catalog Chatbot Frontend

A modern, reactive chatbot interface built with SolidJS for querying the Catalog API using natural language.

## Features

- **Natural Language Queries**: Ask questions about datasets, keywords, schema, and lineage
- **Real-time Responses**: Fast, reactive UI powered by SolidJS
- **Clean Interface**: Modern chat UI with message history
- **API Integration**: Seamless connection to FastAPI backend
- **Health Monitoring**: Connection status indicator
- **Auto-scroll**: Automatically scrolls to latest messages

## Tech Stack

- **SolidJS** - Reactive UI framework with fine-grained reactivity
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **CSS3** - Modern styling with animations

## Prerequisites

- Node.js 18+ and npm
- Running Catalog API server (FastAPI backend)
- API key for the Catalog API

## Installation

1. Install dependencies:

```bash
cd client
npm install
```

2. Configure environment variables:

```bash
cp .env.example .env
```

3. Edit `.env` and add your API key:

```env
VITE_API_KEY=your-actual-api-key-here
```

## Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

The dev server includes a proxy that forwards `/api/*` requests to `http://localhost:8000`, so make sure your FastAPI server is running on port 8000.

## Build for Production

Build the optimized production bundle:

```bash
npm run build
```

Preview the production build:

```bash
npm run serve
```

## Project Structure

```
client/
├── src/
│   ├── components/
│   │   ├── Chat.tsx           # Main chat container
│   │   ├── ChatInput.tsx      # Message input component
│   │   └── MessageList.tsx    # Message display component
│   ├── services/
│   │   └── api.ts            # API client service
│   ├── types.ts              # TypeScript type definitions
│   ├── App.tsx               # Root application component
│   ├── App.css               # Application styles
│   └── index.tsx             # Application entry point
├── index.html                # HTML template
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
└── package.json             # Dependencies and scripts
```

## Usage

### Example Queries

Try asking the chatbot questions like:

- "What datasets are available?"
- "Show me the schema for the Fire_Perimeters dataset"
- "What are the most common keywords?"
- "What fields are in the Watersheds table?"
- "Show me the lineage for the FIRE_NAME field"

### API Endpoints Used

The chatbot primarily uses the `/query` endpoint which provides intelligent routing to:

- Keyword searches
- Dataset listings
- Schema information
- Field lineage
- Dataset relationships
- Natural language queries via LLM

## Configuration

### Environment Variables

- `VITE_API_BASE_URL` - Base URL for the API (default: `/api`)
- `VITE_API_KEY` - Your API key for authentication

### Proxy Configuration

In development, the Vite dev server proxies API requests:

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ''),
  },
}
```

For production, configure your web server to proxy `/api` requests to your FastAPI backend.

## Troubleshooting

### Connection Issues

If you see "Disconnected" status:

1. Ensure the FastAPI server is running on port 8000
2. Check that your API key is correct in `.env`
3. Verify the proxy configuration in `vite.config.ts`

### API Key Errors

If you get "Invalid API key" errors:

1. Check that `X_API_KEY` is set in the server's environment
2. Verify your `VITE_API_KEY` matches the server's key
3. The API key is sent via the `x-api-key` header

## Development Notes

### SolidJS Features Used

- **Signals**: For reactive state management (`createSignal`)
- **Effects**: For auto-scroll and side effects (`createEffect`)
- **Control Flow**: Efficient list rendering (`For` component)
- **Lifecycle**: Connection check on mount (`onMount`)

### Performance

SolidJS's fine-grained reactivity ensures:

- Only changed messages re-render
- Minimal bundle size (~7KB framework)
- Fast initial load and interactions
- Efficient memory usage

## Future Enhancements

Potential improvements:

- [ ] Streaming responses (token-by-token display)
- [ ] Message persistence (localStorage)
- [ ] Markdown rendering for formatted responses
- [ ] Code syntax highlighting
- [ ] File upload for schema import
- [ ] Dark mode toggle
- [ ] Message search and filtering
- [ ] Export chat history

## License

Part of the Catalog project - see parent README for license information.
