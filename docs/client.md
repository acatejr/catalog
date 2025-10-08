---
title: Streamlit Web Client
description: Web-based chat interface built with Streamlit for conversational interaction with the Catalog API
tags:
  - streamlit
  - client
  - ui
  - chat
  - frontend
  - web-app
---

# Streamlit Client

## Overview

The Catalog Streamlit client provides a web-based chat interface for interacting with the Catalog API. Built with Streamlit, it offers an intuitive conversational UI for querying the catalog system using natural language.

## Features

- **Chat Interface**: Modern chat-style interface with message history
- **Real-time Responses**: Direct integration with the Catalog API
- **Error Handling**: Graceful handling of timeouts and API errors
- **Session Management**: Maintains conversation history within a session
- **Configurable**: Environment-based configuration for API endpoints

## Installation

### Prerequisites

- Python 3.8 or higher
- Access to a running Catalog API instance
- Valid API key for authentication

### Setup

1. Navigate to the client directory:
```bash
cd slclient
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

The required dependencies are:
- `streamlit` - Web framework for the chat interface
- `openai` - OpenAI Python client library
- `httpx` - HTTP client for API requests

## Configuration

The client uses environment variables for configuration:

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `X_API_KEY` | API key for authenticating with the Catalog API | `your-secret-api-key` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CATALOG_API_BASE_URL` | Base URL of the Catalog API | `http://127.0.0.1:8000` |

### Setting Environment Variables

**Linux/macOS:**
```bash
export X_API_KEY="your-api-key"
export CATALOG_API_BASE_URL="http://localhost:8000"
```

**Windows (PowerShell):**
```powershell
$env:X_API_KEY="your-api-key"
$env:CATALOG_API_BASE_URL="http://localhost:8000"
```

**Using .env file:**
```bash
# Create .env file in slclient directory
X_API_KEY=your-api-key
CATALOG_API_BASE_URL=http://localhost:8000
```

## Usage

### Starting the Client

Run the Streamlit application:
```bash
streamlit run app.py
```

The client will:
1. Start a local web server (default: http://localhost:8501)
2. Automatically open your default browser
3. Display the Catalog Chatbot interface

### Using the Chat Interface

1. **Ask Questions**: Type your question in the chat input box at the bottom
2. **View Responses**: The assistant's response appears in the chat history
3. **Continue Conversation**: Your entire conversation history is preserved during the session
4. **New Session**: Refresh the page to start a new conversation

### Example Queries

```
"What fire related data sets are in the catalog?"
"Tell me about hydrologic data in the catalog"
"What are important keywords used in the catalog?"
```

## Architecture

### Code Structure

The application (`app.py`) consists of the following key components:

#### 1. Imports and Configuration
```python
from openai import OpenAI
import streamlit as st
import httpx
import os, json
```

#### 2. Environment Setup
- Loads API key from environment
- Constructs query URL from base URL

#### 3. Streamlit UI Setup
- Page title and configuration
- Session state initialization for message history

#### 4. Chat Display Loop
- Iterates through message history
- Displays previous messages with appropriate roles

#### 5. Input Handling
- Captures user input via `st.chat_input()`
- Adds messages to session state
- Displays user message immediately

#### 6. API Integration
- Makes GET request to `/query` endpoint
- Includes API key in headers
- Handles response parsing and errors

### Session State

The client uses Streamlit's session state to maintain conversation history:

```python
st.session_state.messages = [
    {"role": "user", "content": "User's question"},
    {"role": "assistant", "content": "Assistant's response"}
]
```

### API Communication

The client communicates with the Catalog API using:

- **Method**: HTTP GET
- **Endpoint**: `/query?q={question}`
- **Headers**: `X-API-KEY` for authentication
- **Timeout**: 90 seconds
- **Response Format**: JSON with `response` field

Example request:
```python
response = httpx.get(
    query_url + question,
    headers={"X-API-KEY": X_API_KEY},
    timeout=90.0
)
```

## Error Handling

The client implements comprehensive error handling:

### Timeout Errors
```
Error: Request timed out. Please try again.
```
Occurs when API doesn't respond within 90 seconds.

### HTTP Errors
```
Error: Received status code {code}
```
Occurs when API returns non-200 status code.

### General Exceptions
```
Error: {exception message}
```
Catches any other unexpected errors.

## Troubleshooting

### Common Issues

#### "Connection refused" Error
**Problem**: Cannot connect to the API server.

**Solutions**:
- Verify the API server is running
- Check `CATALOG_API_BASE_URL` is correct
- Ensure no firewall blocking the connection

#### "Unauthorized" or 401 Error
**Problem**: API key is invalid or missing.

**Solutions**:
- Verify `X_API_KEY` environment variable is set
- Confirm the API key matches the server configuration
- Check for typos in the API key

#### "Request timed out" Error
**Problem**: API taking too long to respond.

**Solutions**:
- Check if the API server is under heavy load
- Verify LLM service is responding
- Consider increasing timeout in code if needed

#### Blank Response
**Problem**: API returns 200 but no content.

**Solutions**:
- Check API server logs for errors
- Verify the query endpoint is functioning
- Test the API directly with curl/httpx

### Debug Mode

To see detailed logs, run Streamlit in debug mode:
```bash
streamlit run app.py --logger.level=debug
```

## Development

### Modifying the Client

Key areas for customization:

#### UI Customization
```python
st.title("Your Custom Title")
st.set_page_config(
    page_title="Your Title",
    page_icon="🤖",
    layout="wide"
)
```

#### Timeout Configuration
```python
response = httpx.get(
    query_url + question,
    headers={"X-API-KEY": X_API_KEY},
    timeout=120.0  # Increase to 120 seconds
)
```

#### Response Formatting
Modify the response display:
```python
# Add markdown formatting
answer = f"**Response:** {json.loads(response.text)['response']}"
st.markdown(answer)
```

### Testing Locally

1. Start the API server:
```bash
cd /path/to/catalog
uvicorn catalog.api:app --reload
```

2. In a separate terminal, start the Streamlit client:
```bash
cd slclient
streamlit run app.py
```

3. Access the client at http://localhost:8501

## Deployment

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **HTTPS**: Deploy behind reverse proxy with SSL
3. **Authentication**: Consider adding user authentication layer
4. **Monitoring**: Add logging and error tracking
5. **Scaling**: Use Streamlit Cloud or containerization for scaling

### Docker Deployment

Create a `Dockerfile` in the `slclient` directory:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

Build and run:
```bash
docker build -t catalog-client .
docker run -p 8501:8501 \
  -e X_API_KEY=your-key \
  -e CATALOG_API_BASE_URL=http://api-server:8000 \
  catalog-client
```

## API Reference

### Environment Variables API

The client expects these environment variables:

```python
X_API_KEY = os.getenv("X_API_KEY")
query_url = os.getenv("CATALOG_API_BASE_URL", "http://127.0.0.1:8000") + "/query?q="
```

### Message Format

Messages in session state follow this structure:
```python
{
    "role": "user" | "assistant",
    "content": str
}
```

## Best Practices

1. **Always set API key**: Never commit API keys to version control
2. **Use environment files**: Keep configuration separate from code
3. **Monitor timeouts**: Adjust based on typical query complexity
4. **Test error paths**: Verify error handling works correctly
5. **Clear session state**: Implement clear/reset button for long sessions

## Future Enhancements

Potential improvements for the client:

- **Multi-turn context**: Pass conversation history to API
- **File uploads**: Allow document uploads for context
- **Export conversations**: Save chat history to file
- **Streaming responses**: Show response as it's generated
- **Rich formatting**: Display images, tables, and formatted text
- **User authentication**: Add login/logout functionality
- **Rate limiting**: Prevent API abuse
- **Analytics**: Track usage patterns and common queries

## Related Documentation

- [API Documentation](api.md) - Details on the Catalog API endpoints
- [LLM Integration](llm.md) - How the LLM processes queries
- [Data Storage](data-storage.md) - Backend data architecture
