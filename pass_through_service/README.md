# Django External URL Passthrough Service

## Overview
This is a standalone Flask pass-through service designed to work with the Django External URL Passthrough Middleware functionality. It accepts all HTTP methods and paths, returning detailed request information with an "I heard you!" message.

This service acts as a pass-through endpoint for testing new functionality before implementing it formally in Django.

## Features
- 🎯 **Catch-All Route**: Accepts any HTTP method and path
- 📊 **Request Details**: Returns comprehensive request information
- 🌐 **Multi-Format**: Supports both JSON (for APIs) and HTML (for browsers)
- 🔊 **Echo Endpoint**: Special POST endpoint for testing
- ❤️ **Health Check**: Service status endpoint
- 🚀 **Easy Setup**: Simple Flask application
- 🔄 **Pass-Through Testing**: Perfect for validating new functionality

## Installation & Setup

### 1. Install Dependencies
```bash
cd pass_through_service
pip install -r requirements.txt
```

### 2. Run the Service
```bash
python app.py
```

The service will start on `http://localhost:5000`

## Available Endpoints

### Catch-All Route: `/<any-path>`
- **Methods**: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- **Description**: Accepts any path and method, returns "I heard you!" with request details
- **Examples**:
  - `GET http://localhost:5000/api/test`
  - `POST http://localhost:5000/users/123/update`
  - `DELETE http://localhost:5000/some/deep/path`

### Health Check: `/health`
- **Method**: GET
- **Description**: Simple health check endpoint
- **Response**: Service status and timestamp

### Echo Endpoint: `/echo`
- **Method**: POST
- **Description**: Special endpoint for testing POST requests with data
- **Response**: Enhanced "I heard you!" message with request details

## Testing with Django Middleware

### 1. Update Django Settings
Update your `TARGET_EXTERNAL_URL` in `mysite/settings.py`:

```python
TARGET_EXTERNAL_URL = 'http://localhost:5000'
```

### 2. Start Both Services
1. Start the pass-through service: `python pass_through_service/app.py` (runs on port 5000)
2. Start Django: `python manage.py runserver` (runs on port 8000)

### 3. Test the Middleware
Make requests to non-existent Django URLs:

```bash
# Test GET request
curl http://localhost:8000/non-existent-api/test

# Test POST request with JSON
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "email": "test@example.com"}'

# Test with custom headers
curl http://localhost:8000/custom/path \
  -H "X-Custom-Header: test-value" \
  -H "Authorization: Bearer token123"
```

## Response Format

### JSON Response (Default)
```json
{
  "message": "🎯 I heard you!",
  "pass_through_service": "Django External URL Passthrough Service", 
  "status": "success",
  "request_info": {
    "timestamp": "2025-08-16T12:34:56.789",
    "method": "GET",
    "url": "http://localhost:5000/api/test",
    "path": "/api/test", 
    "headers": {
      "Content-Type": "application/json",
      "X-Custom-Header": "test-value"
    },
    "json": {"key": "value"},
    "data": "raw request body"
  }
}
```

### HTML Response (Browser Requests)
When accessed via browser, returns a formatted HTML page with:
- "I heard you!" message
- Request method, path, timestamp
- Complete request details in formatted JSON
- Clean, readable styling

## Advanced Testing Scenarios

### 1. Test Different HTTP Methods
```python
# PowerShell examples
Invoke-WebRequest -Uri "http://localhost:8000/api/test" -Method GET
Invoke-WebRequest -Uri "http://localhost:8000/api/test" -Method POST -Body '{"test": "data"}'
Invoke-WebRequest -Uri "http://localhost:8000/api/test" -Method PUT -Body '{"update": "data"}'
Invoke-WebRequest -Uri "http://localhost:8000/api/test" -Method DELETE
```

### 2. Test Complex Paths
```bash
curl http://localhost:8000/api/v1/users/123/posts/456/comments
curl http://localhost:8000/deeply/nested/path/with/parameters?id=123&type=test
```

### 3. Test Large Payloads
```bash
curl -X POST http://localhost:8000/api/upload \
  -H "Content-Type: application/json" \
  -d @large-test-file.json
```

## Configuration Options

### Change Port
Edit `app.py` and modify:
```python
PORT = 3000  # Change to desired port
```

### Change Host
Edit `app.py` and modify:
```python
HOST = '127.0.0.1'  # Listen only on localhost
# or
HOST = '0.0.0.0'    # Listen on all interfaces
```

### Enable/Disable Debug Mode
```python
DEBUG = False  # Disable debug mode for production-like testing
```

## Troubleshooting

### Port Already in Use
If port 5000 is busy:
1. Change `PORT = 5001` in `app.py`
2. Update Django's `TARGET_EXTERNAL_URL = 'http://localhost:5001'`

### Flask Not Installed
```bash
pip install flask
```

### Connection Refused
1. Ensure pass-through service is running: `python app.py`
2. Check firewall settings
3. Verify port is not blocked

## Use Cases

### 1. Middleware Development
- Test middleware logic before implementing external service
- Verify request forwarding works correctly
- Debug header and body transmission

### 2. API Prototyping  
- Mock external API responses
- Test error handling scenarios
- Validate request formats

### 3. Integration Testing
- End-to-end testing of external URL passthrough
- Performance testing with realistic payloads
- Multi-environment testing

## Sample Test Script

Create `test_middleware.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"  # Django server
TEST_ENDPOINTS = [
    "/api/test",
    "/users/123", 
    "/non/existent/path",
    "/deeply/nested/api/endpoint"
]

def test_middleware():
    for endpoint in TEST_ENDPOINTS:
        # Test GET
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"GET {endpoint}: {response.status_code}")
        
        # Test POST
        data = {"test": "data", "endpoint": endpoint}
        response = requests.post(
            f"{BASE_URL}{endpoint}", 
            json=data,
            headers={"X-Test": "middleware"}
        )
        print(f"POST {endpoint}: {response.status_code}")
        print(f"Response: {response.json()['message']}")
        print("-" * 50)

if __name__ == "__main__":
    test_middleware()
```

Run with: `python test_middleware.py`

---

**Ready to hear your Django requests! 🎯**
