# logWise Backend

A FastAPI-based backend for Docker container log analysis with RAG (Retrieval-Augmented Generation) capabilities using Gemini via LiteLLM.

## Features

- **Real-time Log Ingestion**: Automatically streams and processes Docker container logs
- **Vector Storage**: Uses ChromaDB for efficient log chunk storage and retrieval
- **RAG-powered Queries**: Ask natural language questions about container logs
- **WebSocket Streaming**: Real-time log streaming via WebSocket
- **RESTful API**: Complete REST API for container management and log analysis

## Architecture

```
app/
├── main.py              # FastAPI application entry point
├── api/                 # API routes
│   ├── containers.py    # Container management endpoints
│   ├── logs.py         # Log streaming and retrieval
│   └── query.py        # RAG query endpoints
├── ingestion/          # Log ingestion pipeline
│   ├── watcher.py      # Docker event monitoring
│   └── streamer.py     # Log streaming and processing
├── rag/               # RAG components
│   ├── llm_client.py  # LiteLLM client for Gemini
│   └── retriever.py   # Vector search and retrieval
└── storage/           # Data storage
    └── vector_store.py # ChromaDB integration
```

## Quick Start

### 1. Environment Setup

Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Using Docker

```bash
# Build and run
docker-compose up --build

# Or build manually
docker build -t logwise-backend .
docker run -p 8000:8000 --env-file .env logwise-backend
```

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health status

### Containers
- `GET /api/containers` - List all containers
- `GET /api/containers/{container_id}` - Get container details

### Logs
- `GET /api/logs/raw` - Get raw logs with optional filtering
- `GET /api/logs/stats` - Get log statistics
- `WS /api/logs/stream` - WebSocket for real-time log streaming

### RAG Queries
- `POST /api/logs/query` - Query logs using natural language
- `GET /api/logs/query/suggestions` - Get suggested questions
- `GET /api/logs/query/stats` - Get query statistics

## Example Usage

### List Containers
```bash
curl http://localhost:8000/api/containers
```

### Query Logs
```bash
curl -X POST http://localhost:8000/api/logs/query \
  -H "Content-Type: application/json" \
  -d '{
    "container_id": "your_container_id",
    "question": "What errors occurred in the logs?",
    "k": 8
  }'
```

### Get Raw Logs
```bash
curl "http://localhost:8000/api/logs/raw?container_id=your_container_id&tail=100"
```

## Testing

Run the smoke tests:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run example usage
python example_usage.py
```

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required. Your Gemini API key
- `CHROMA_PERSIST_DIR`: Optional. ChromaDB persistence directory (default: `./chroma_db`)
- `LOG_BUFFER_SIZE`: Optional. Log chunk size in characters (default: 300)
- `MAX_QUERY_RESULTS`: Optional. Maximum results for queries (default: 8)

### LiteLLM Models

The backend uses LiteLLM for model access:

- **Completions**: `gemini/ultra`
- **Embeddings**: `gemini/embeddings`

## Development

### Project Structure

- **FastAPI**: Modern async web framework
- **ChromaDB**: Vector database for log storage
- **LiteLLM**: Unified LLM interface
- **Docker SDK**: Container management
- **WebSocket**: Real-time communication

### Key Components

1. **DockerWatcher**: Monitors container events and manages log streamers
2. **LogStreamer**: Streams, chunks, and embeds container logs
3. **RAGRetriever**: Handles vector search and context retrieval
4. **VectorStore**: ChromaDB wrapper for log storage

### Adding New Features

1. **New API Routes**: Add to `app/api/`
2. **New Models**: Add to appropriate module with Pydantic
3. **New Services**: Add to appropriate package
4. **Tests**: Add to `tests/` directory

## Troubleshooting

### Common Issues

1. **Docker Connection**: Ensure Docker daemon is running
2. **API Key**: Verify `GEMINI_API_KEY` is set correctly
3. **Port Conflicts**: Check if port 8000 is available
4. **Permissions**: Ensure Docker socket access

### Logs

Check application logs for detailed error information:

```bash
# Docker logs
docker-compose logs backend

# Direct logs
uvicorn app.main:app --log-level debug
```

## License

This project is part of the logWise Docker extension. 