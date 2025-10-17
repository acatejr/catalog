---
title: Catalog REST API
description: FastAPI REST API endpoints for querying the catalog system with API key authentication
tags:
  - api
  - rest
  - fastapi
  - authentication
  - endpoints
  - http
---

# API

## Overview

The Catalog API is a FastAPI-based REST API that provides programmatic access to the catalog's query functionality. It allows clients to interact with the AI agent through HTTP endpoints, enabling integration with other applications and services.

**Base Information:**

- **Framework:** FastAPI
- **Version:** 0.0.1
- **Title:** Catalog API

## Authentication

The API uses API key authentication to secure endpoints. The API key must be provided in the request headers.

### Configuration

The API expects the following environment variable to be set:

- `X_API_KEY`: The API key required for authentication

### Authentication Method

Authentication is implemented using the `x-api-key` header:

```bash
x-api-key: your-api-key-here
```

### Security Implementation

The API implements authentication through a dependency injection pattern:

- **Header Name:** `x-api-key`
- **Validation:** Automatic validation on protected endpoints
- **Error Response:** Returns HTTP 401 (Unauthorized) for invalid or missing API keys

## Endpoints

### Health Check

Check the API's health status and current timestamp.

**Endpoint:** `GET /health`

**Tags:** `Health`

**Authentication:** Not required

**Parameters:** None

**Response:**

```json
{
  "status": "ok - 2025-10-08 08:56:04"
}
```

**Response Fields:**

- `status` (string): Health status with timestamp in format "ok - YYYY-MM-DD HH:MM:SS"

**Example Request:**

```bash
curl -X GET "http://localhost:8000/health"
```

**Example Response:**

```json
{
  "status": "ok - 2025-10-08 08:56:04"
}
```

---

### Query

Submit a query to the AI agent and receive a response.

**Endpoint:** `GET /query`

**Tags:** `Query`

**Authentication:** Required (via `x-api-key` header)

**Parameters:**

| Parameter | Type   | Required | Location | Description                          |
|-----------|--------|----------|----------|--------------------------------------|
| q         | string | Yes      | Query    | The query string to send to the AI agent |

**Response:**

```json
{
  "query": "your query text",
  "response": "AI agent's response"
}
```

**Response Fields:**

- `query` (string): The original query string submitted
- `response` (string): The AI agent's response to the query

**Example Request:**

```bash
curl -X GET "http://localhost:8000/query?q=What%20is%20the%20capital%20of%20France?" \
  -H "x-api-key: your-api-key-here"
```

**Example Response:**

```json
{
  "query": "What is the capital of France?",
  "response": "The capital of France is Paris."
}
```

## Error Handling

### Authentication Errors

**HTTP 401 - Unauthorized**

Returned when the API key is missing or invalid.

**Response:**

```json
{
  "detail": "Invalid API key"
}
```

**Causes:**

- Missing `x-api-key` header
- Incorrect API key value
- API key doesn't match the configured `X_API_KEY` environment variable

### Validation Errors

**HTTP 422 - Unprocessable Entity**

Returned when request parameters are invalid or missing.

**Example Response:**

```json
{
  "detail": [
    {
      "loc": ["query", "q"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Implementation Details

### Dependencies

The API uses the following key dependencies:

- **FastAPI:** Web framework for building the API
- **llm.ChatBot:** AI agent for processing queries (imported from `src/llm.py`)
- **fastapi.security.api_key:** API key authentication

### Code Structure

```python
# API initialization
api = FastAPI(title="Catalog API", version="0.0.1")

# API key verification dependency
def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    # Validates API key against environment variable
    
# Health endpoint - no authentication required
@api.get("/health", tags=["Health"])
async def health():
    # Returns current timestamp and status
    
# Query endpoint - authentication required
@api.get("/query", tags=["Query"])
async def query(q: str):
    # Processes query through ChatBot and returns response
```

### ChatBot Integration

The `/query` endpoint integrates with the `ChatBot` class from the `catalog.llm` module:

1. Creates a new `ChatBot` instance for each request
2. Passes the query string to the `chat()` method
3. Returns the AI-generated response

## Usage Examples

### Python (using requests)

```python
import requests

# API configuration
API_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

# Health check
response = requests.get(f"{API_URL}/health")
print(response.json())

# Query with authentication
headers = {"x-api-key": API_KEY}
params = {"q": "What is the capital of France?"}
response = requests.get(f"{API_URL}/query", headers=headers, params=params)
print(response.json())
```

### JavaScript (using fetch)

```javascript
const API_URL = "http://localhost:8000";
const API_KEY = "your-api-key-here";

// Health check
fetch(`${API_URL}/health`)
  .then(response => response.json())
  .then(data => console.log(data));

// Query with authentication
fetch(`${API_URL}/query?q=${encodeURIComponent("What is the capital of France?")}`, {
  headers: {
    "x-api-key": API_KEY
  }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# Query with authentication
curl -X GET "http://localhost:8000/query?q=What%20is%20the%20capital%20of%20France?" \
  -H "x-api-key: your-api-key-here"
```

## Running the API

### Environment Setup

Before running the API, ensure the `X_API_KEY` environment variable is set:

```bash
export X_API_KEY="your-secure-api-key"
```

### Starting the Server

Use the CLI command to run the API:

```bash
PYTHONPATH=src python src/cli.py run-api
```

Or use uvicorn directly:

```bash
cd src
uvicorn api:api --host 0.0.0.0 --port 8000 --reload
```

Or with Docker Compose:

```bash
docker compose up -d
```

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** Available at `http://localhost:8000/docs`
- **ReDoc:** Available at `http://localhost:8000/redoc`

These interfaces provide:

- Interactive endpoint testing
- Request/response schemas
- Authentication testing
- Example requests and responses

## Security Considerations

### API Key Management

- Store API keys securely using environment variables
- Never commit API keys to version control
- Rotate API keys regularly
- Use different keys for different environments (development, staging, production)

### Best Practices

1. **Use HTTPS:** Always use HTTPS in production to encrypt API keys in transit
2. **Rate Limiting:** Consider implementing rate limiting to prevent abuse
3. **Input Validation:** The query parameter should be validated and sanitized
4. **Logging:** Avoid logging API keys or sensitive information
5. **Error Messages:** Don't expose internal system details in error messages

## Future Enhancements

Potential improvements to consider:

- POST endpoint for complex queries with request body
- Pagination for results
- Rate limiting implementation
- Multiple API key support with different permission levels
- Query history and analytics
- Streaming responses for long-running queries
- WebSocket support for real-time interactions
- Caching layer for common queries
