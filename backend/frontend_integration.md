# Frontend Integration Guide

## Backend API Endpoints

Your backend is now running on `http://localhost:8000` with the following endpoints:

### Health & Status
- `GET /health` - Health check
- `GET /` - Root endpoint

### Containers
- `GET /api/containers` - List all containers
- `GET /api/containers/{container_id}` - Get specific container info

### Logs
- `GET /api/logs/query/suggestions` - Get query suggestions
- `GET /api/logs/stats` - Get log statistics

### Query
- `POST /api/logs/query` - Query logs with RAG

## Frontend Integration

### 1. Update Frontend API Base URL

In your frontend, update the API base URL to point to the backend:

```typescript
// In your frontend API configuration
const API_BASE_URL = 'http://localhost:8000';
```

### 2. Example API Calls

```typescript
// Get containers
const getContainers = async () => {
  const response = await fetch(`${API_BASE_URL}/api/containers`);
  return response.json();
};

// Query logs
const queryLogs = async (containerId: string, question: string) => {
  const response = await fetch(`${API_BASE_URL}/api/logs/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      container_id: containerId,
      question: question,
      k: 8
    }),
  });
  return response.json();
};

// Get query suggestions
const getSuggestions = async () => {
  const response = await fetch(`${API_BASE_URL}/api/logs/query/suggestions`);
  return response.json();
};
```

### 3. CORS Configuration

The backend already has CORS configured to allow all origins (`*`). For production, you should configure it more restrictively.

### 4. Error Handling

```typescript
const apiCall = async (endpoint: string, options?: RequestInit) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
};
```

## Testing the Integration

1. **Start the backend:**
   ```bash
   cd backend
   python run.py
   ```

2. **Start the frontend:**
   ```bash
   cd ui
   npm run dev
   ```

3. **Test the connection:**
   - Open browser to `http://localhost:3000`
   - Check browser console for any CORS errors
   - Try making API calls from the frontend

## Common Issues

### CORS Errors
- Backend CORS is already configured
- Make sure frontend is calling the correct URL (`http://localhost:8000`)

### Connection Refused
- Ensure backend is running on port 8000
- Check if Docker daemon is running

### API Errors
- Check the backend logs for detailed error messages
- Use the test scripts to verify backend functionality

## Next Steps

1. Update your frontend to use the new API endpoints
2. Test the container listing functionality
3. Implement the chat interface using the query endpoint
4. Add error handling and loading states
5. Test with real Docker containers 