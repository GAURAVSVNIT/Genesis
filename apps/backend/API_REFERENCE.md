# Genesis Backend - Complete API Reference

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://genesis-backend-YOUR_ID.run.app`

## API Documentation

### Swagger UI
- **URL**: `http://localhost:8000/docs`
- **Description**: Interactive API documentation and testing

### ReDoc
- **URL**: `http://localhost:8000/redoc`
- **Description**: Alternative API documentation

## Content Generation Endpoints

### Generate Content
**POST** `/v1/content/generate`

Generate content using Vertex AI with integrated guardrails and embeddings.

**Request Body:**
```json
{
  "prompt": "Write a blog post about AI ethics",
  "safety_level": "moderate",
  "conversation_history": []
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "content": "Generated content here...",
  "safety_checks": {
    "length": "safe",
    "harmful_content": "safe",
    "prompt_injection": "safe",
    "spam": "safe"
  },
  "tokens_used": null
}
```

**Errors:**
- 400: Invalid request
- 500: Content generation failed

---

### Content Health Check
**GET** `/v1/content/health`

Check if content generation service is available.

**Response (200 OK):**
```json
{
  "status": "ok",
  "model": "gemini-2.0-flash",
  "platform": "Vertex AI",
  "test_response": "..."
}
```

**Errors:**
- 503: Service unavailable

---

### List Available Models
**GET** `/v1/content/models`

Get list of available Vertex AI models.

**Response (200 OK):**
```json
{
  "models": [
    {
      "name": "gemini-2.0-flash",
      "description": "Latest fast Gemini model",
      "context_window": 100000
    },
    {
      "name": "gemini-1.5-pro",
      "description": "High-capability Gemini model",
      "context_window": 1000000
    },
    {
      "name": "gemini-1.5-flash",
      "description": "Fast Gemini model",
      "context_window": 1000000
    }
  ]
}
```

---

## Guardrails / Safety Endpoints

### Validate Message Safety
**POST** `/v1/guardrails/validate-message`

Check if a user message is safe according to guardrails.

**Request Body:**
```json
{
  "content": "What is machine learning?",
  "role": "user",
  "safety_level": "moderate"
}
```

**Response (200 OK):**
```json
{
  "is_safe": true,
  "reason": "Message passed all safety checks",
  "score": 0.95,
  "filtered_text": "What is machine learning?"
}
```

**Parameters:**
- `content` (string, required): Message to validate
- `role` (string): "user" or "assistant"
- `safety_level` (string): "strict", "moderate", or "permissive"

---

### Validate System Prompt
**POST** `/v1/guardrails/validate-prompt`

Check if a system prompt is safe (very strict validation).

**Request Body:**
```json
{
  "prompt": "You are a helpful AI assistant.",
  "safety_level": "strict"
}
```

**Response (200 OK):**
```json
{
  "is_safe": true,
  "reason": "System prompt is safe",
  "score": 0.98,
  "filtered_text": "You are a helpful AI assistant."
}
```

---

### Analyze Safety in Detail
**POST** `/v1/guardrails/analyze`

Get detailed safety analysis with breakdown of all checks.

**Request Body:**
```json
{
  "content": "Your message here"
}
```

**Response (200 OK):**
```json
[
  {
    "type": "length_check",
    "status": "safe",
    "score": 1.0,
    "details": "Text length is within acceptable range"
  },
  {
    "type": "harmful_content",
    "status": "safe",
    "score": 0.99,
    "details": "No harmful patterns detected"
  },
  {
    "type": "prompt_injection",
    "status": "safe",
    "score": 0.99,
    "details": "No injection patterns detected"
  },
  {
    "type": "spam",
    "status": "safe",
    "score": 0.98,
    "details": "No spam indicators detected"
  }
]
```

---

### Get Available Safety Levels
**GET** `/v1/guardrails/safety-levels`

List all available safety levels and their descriptions.

**Response (200 OK):**
```json
{
  "levels": [
    {
      "name": "strict",
      "description": "Maximum filtering for sensitive content"
    },
    {
      "name": "moderate",
      "description": "Balanced filtering (recommended)"
    },
    {
      "name": "permissive",
      "description": "Minimal filtering for creative content"
    }
  ]
}
```

---

## Embeddings Endpoints

### Generate Single Embedding
**POST** `/v1/embeddings/embed`

Generate a vector embedding for text.

**Request Body:**
```json
{
  "text": "Your text here"
}
```

**Response (200 OK):**
```json
{
  "embedding": [0.123, 0.456, ...],
  "dimensions": 384,
  "model": "all-MiniLM-L6-v2",
  "text_length": 15
}
```

---

### Generate Multiple Embeddings
**POST** `/v1/embeddings/embed-batch`

Generate embeddings for multiple texts.

**Request Body:**
```json
{
  "texts": [
    "First text",
    "Second text",
    "Third text"
  ]
}
```

**Response (200 OK):**
```json
{
  "embeddings": [
    [0.123, 0.456, ...],
    [0.789, 0.012, ...],
    [0.345, 0.678, ...]
  ],
  "count": 3,
  "dimensions": 384,
  "model": "all-MiniLM-L6-v2"
}
```

---

### Embeddings Health Check
**GET** `/v1/embeddings/health`

Check if embeddings service is operational.

**Response (200 OK):**
```json
{
  "status": "ok",
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384
}
```

---

## Blog Generation Endpoints

### Generate Blog
**POST** `/v1/blog/generate`

Generate a blog post.

**Request Body:**
```json
{
  "topic": "AI Ethics",
  "style": "formal",
  "length": "medium"
}
```

**Response (200 OK):**
```json
{
  "id": "blog-123",
  "title": "The Ethics of Artificial Intelligence",
  "content": "...",
  "status": "published"
}
```

---

### Get Blog
**GET** `/v1/blog/{blog_id}`

Retrieve a generated blog post.

**Response (200 OK):**
```json
{
  "id": "blog-123",
  "title": "The Ethics of Artificial Intelligence",
  "content": "...",
  "created_at": "2024-01-01T00:00:00Z",
  "status": "published"
}
```

---

## Guest/Authentication Endpoints

### Guest Login
**POST** `/v1/guest/login`

Login as a guest user.

**Response (200 OK):**
```json
{
  "session_id": "guest-123",
  "user_id": "user-123",
  "expires_in": 3600
}
```

---

## Agent Orchestration Endpoints

### Orchestrate Multi-Agent Task
**POST** `/v1/agent/orchestrate`

Run a complex task with multiple AI agents.

**Request Body:**
```json
{
  "task": "Write and review a blog post about AI",
  "agents": ["writer", "reviewer"],
  "parameters": {}
}
```

**Response (200 OK):**
```json
{
  "task_id": "task-123",
  "status": "completed",
  "result": "..."
}
```

---

### Get Agent Status
**GET** `/v1/agent/status/{task_id}`

Get status of an agent task.

**Response (200 OK):**
```json
{
  "task_id": "task-123",
  "status": "in-progress",
  "progress": 75,
  "current_agent": "reviewer"
}
```

---

## Health & Status Endpoints

### General Health Check
**GET** `/v1/health`

Check overall API health.

**Response (200 OK):**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### Redis Health Check
**GET** `/v1/health/redis`

Check Redis connectivity.

**Response (200 OK):**
```json
{
  "status": "ok",
  "redis": "connected"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request body"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service is currently unavailable"
}
```

---

## Request/Response Models

### SafetyReport
```python
{
  "is_safe": bool,           # Whether message is safe
  "reason": str,             # Explanation
  "score": float,            # Safety score 0-1
  "filtered_text": str       # Cleaned text (optional)
}
```

### GenerateContentRequest
```python
{
  "prompt": str,                    # Content prompt
  "safety_level": str,              # "strict", "moderate", "permissive"
  "conversation_history": List[
    {
      "role": str,                  # "user" or "assistant"
      "content": str                # Message text
    }
  ]
}
```

### GenerateContentResponse
```python
{
  "success": bool,           # Whether generation succeeded
  "content": str,            # Generated content
  "safety_checks": dict,     # Safety check results
  "tokens_used": int|null    # Token count if available
}
```

---

## Authentication

### Current Status
- ❌ **Not Yet Implemented**
- API endpoints are currently public
- Recommended: Add before production deployment

### When to Add
- Before exposing API publicly
- When adding multi-user support
- When implementing usage tracking

### Options
- API Keys
- JWT Tokens
- OAuth 2.0
- Service-to-Service (mTLS)

---

## Rate Limiting

### Current Status
- ❌ **Not Yet Implemented**
- Available through Cloud Armor (GCP)

### Recommended
- 100 requests/minute per IP (development)
- 1000 requests/minute per user (production)
- 10000 requests/minute per service

---

## CORS Configuration

### Current Configuration
- **Allowed Origins**: `http://localhost:3000`
- **Allowed Methods**: All (`GET`, `POST`, `PUT`, `DELETE`, etc.)
- **Allowed Headers**: All
- **Credentials**: Allowed

### Update for Production
```python
# In main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Pagination

### Supported Endpoints
- None yet (can be added to list endpoints)

### Format (When Added)
```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 100,
  "pages": 5
}
```

---

## Filtering & Search

### Supported Endpoints
- None yet

### Format (When Added)
```bash
GET /v1/endpoint?filter=key:value&search=query&sort=-created_at
```

---

## API Versioning

### Current Version
- **Version**: 1.0.0
- **Base Path**: `/v1/*`

### Future Versions
- Plan for v2 when major breaking changes needed
- Support previous version for 6 months

---

## Testing Endpoints

### Using curl
```bash
# Health check
curl http://localhost:8000/v1/health

# Generate content
curl -X POST http://localhost:8000/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "safety_level": "moderate"}'

# Validate message
curl -X POST http://localhost:8000/v1/guardrails/validate-message \
  -H "Content-Type: application/json" \
  -d '{"content": "Test", "role": "user"}'
```

### Using Python requests
```python
import requests

# Health check
resp = requests.get("http://localhost:8000/v1/health")

# Generate content
resp = requests.post(
    "http://localhost:8000/v1/content/generate",
    json={
        "prompt": "Write something",
        "safety_level": "moderate",
        "conversation_history": []
    }
)
```

### Using fetch (JavaScript)
```javascript
// Health check
fetch("http://localhost:8000/v1/health")
  .then(r => r.json())
  .then(console.log);

// Generate content
fetch("http://localhost:8000/v1/content/generate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    prompt: "Write something",
    safety_level: "moderate",
    conversation_history: []
  })
})
  .then(r => r.json())
  .then(console.log);
```

---

## Webhook Support

### Current Status
- ❌ **Not Implemented**

### When to Add
- For async processing
- For large batch jobs
- For real-time notifications

---

## Deprecated Endpoints

### Current Status
- None (Version 1.0.0)

### Deprecation Policy
- 6 months notice before removal
- Include `Deprecation` header in responses
- Provide migration guide

---

## API Changelog

### Version 1.0.0 (2024)
- ✅ Content generation API
- ✅ Guardrails safety API
- ✅ Embeddings API
- ✅ Blog generation API
- ✅ Agent orchestration API
- ✅ Health check endpoints

### Version 1.1.0 (Planned)
- [ ] Vector similarity search
- [ ] Conversation persistence
- [ ] Usage analytics
- [ ] Rate limiting

### Version 2.0.0 (Future)
- [ ] Authentication
- [ ] Multi-tenancy
- [ ] Advanced features

---

## Support & Issues

### Reporting Issues
1. Check [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
2. Check endpoint documentation above
3. Review [BACKEND_README.md](./BACKEND_README.md)
4. Check logs in Cloud Logging

### Common Issues
- **401**: Check authentication (if enabled)
- **400**: Check request format
- **500**: Check server logs
- **503**: Service may be cold (Cloud Run)

---

**Last Updated**: 2024
**API Version**: 1.0.0
**Status**: Production Ready
