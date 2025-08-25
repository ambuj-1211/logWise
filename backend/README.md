# Dockerative Extension Backend

A comprehensive Docker log analysis system with real-time monitoring, vector database storage, and RAG-powered querying capabilities.

## 🚀 System Overview

This backend system provides a complete pipeline for Docker container monitoring, log analysis, and intelligent querying using advanced AI techniques.

## 🏗️ Architecture & Flow

### 1. Docker Container Monitoring Service
**Purpose**: Watch the system to get information about running Docker containers and store logs in the database.

**Components**:
- **DockerWatcher** (`app/ingestion/watcher.py`): Monitors Docker events and manages container lifecycle
- **EnhancedLogStreamer** (`app/ingestion/streamer.py`): Streams and processes container logs in real-time

**Process Flow**:
```
Docker Events → DockerWatcher → LogStreamer → Log Processing → Database Storage
     ↓              ↓              ↓              ↓              ↓
Container    Event Detection   Log Streaming   Chunking &     ChromaDB
Lifecycle    & Management      & Buffering     Embedding      Storage
```

**Key Features**:
- Real-time Docker event monitoring
- Automatic container lifecycle management
- Intelligent log chunking with overlap
- Log level detection and severity scoring
- Performance tracking and statistics

### 2. Vector Database Creation & Storage
**Purpose**: Create and store processed log data in a vector database for efficient retrieval.

**Components**:
- **VectorStore** (`app/storage/vector_store.py`): ChromaDB integration with multiple collections
- **ChromaDB**: Vector database with three specialized collections

**Collections**:
1. **Main Collection** (`docker_logs_main`): Flat indexing for exact similarity
2. **Fast Collection** (`docker_logs_fast`): ANN indexing for approximate search
3. **Error Collection** (`docker_logs_errors`): Specialized error analysis

**Storage Process**:
```
Log Chunks → Embedding Generation → Vector Storage → Metadata Indexing
     ↓              ↓                    ↓              ↓
Text Content   AI Embeddings      ChromaDB Vectors   Search Indexes
```

### 3. Query Endpoint Service
**Purpose**: Expose API endpoints to receive queries from clients.

**Components**:
- **FastAPI Application** (`app/main.py`): Main web server
- **API Routes** (`app/api/`): RESTful endpoints for client interaction

**Available Endpoints**:
```
GET  /                    - Health check
GET  /health             - Detailed health status
GET  /api/containers     - List all containers
GET  /api/containers/{id} - Get container details
POST /api/logs/query     - RAG-powered log querying
GET  /api/logs/stats     - Log statistics
GET  /api/logs/query/suggestions - Query suggestions
```

### 4. RAG Query Processing Service
**Purpose**: Process client queries, embed them, perform similarity search, and generate responses.

**Components**:
- **RAGRetriever** (`app/rag/retriever.py`): Two-stage retrieval pipeline
- **LLMClient** (`app/rag/llm_client.py`): AI model integration (Voyage AI + Gemini)

**Query Processing Flow**:
```
User Query → Query Embedding → Vector Search → Reranking → Context Building → LLM Generation → Response
     ↓              ↓              ↓              ↓              ↓              ↓              ↓
Natural      Vector      Similar        Relevance    Prompt        AI Model      Generated
Language    Embedding   Documents      Ranking      Context       Processing    Answer
```

**Two-Stage Pipeline**:
1. **Vector Similarity Search**: Find relevant log chunks using embeddings
2. **Reranking**: Use Voyage AI to rank results by relevance
3. **Context Building**: Create comprehensive prompt with retrieved context
4. **Answer Generation**: Generate natural language response using AI

### 5. Frontend Integration
**Purpose**: Provide seamless integration with the frontend application.

**Integration Points**:
- **RESTful APIs**: Standard HTTP endpoints for all operations
- **CORS Support**: Cross-origin resource sharing enabled
- **Error Handling**: Comprehensive error responses
- **Real-time Updates**: WebSocket support for live data

**Frontend API Usage**:
```typescript
// Get containers
const containers = await fetch('/api/containers').then(r => r.json());

// Query logs with RAG
const response = await fetch('/api/logs/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    container_id: 'container_id',
    question: 'What errors occurred?',
    k: 8
  })
});
```

## 🔧 Setup & Installation

### Prerequisites
- Python 3.8+
- Docker daemon running
- API keys for AI services

### Environment Configuration
```bash
# Required API Keys
export VOYAGE_API_KEY="your_voyage_api_key"
export GEMINI_API_KEY="your_gemini_api_key"  # Optional

# Optional Configuration
export CHROMA_PERSIST_DIR="./chroma_db"
export LOG_BUFFER_SIZE=300
export MAX_QUERY_RESULTS=8
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -t dockerative-backend .
docker run -p 8000:8000 --env-file .env dockerative-backend

# Or with docker-compose
docker-compose up --build
```

## 📊 Key Features

### Real-time Log Monitoring
- Automatic container event detection
- Continuous log streaming and processing
- Intelligent chunking with context preservation
- Performance monitoring and statistics

### Advanced Vector Search
- Multiple indexing strategies (Flat, ANN)
- Specialized error collection
- Container-specific filtering
- Metadata-based search capabilities

### RAG-powered Querying
- Two-stage retrieval pipeline
- Voyage AI embeddings and reranking
- Context-aware answer generation
- Query suggestions and statistics

### Comprehensive API
- RESTful endpoints for all operations
- WebSocket support for real-time updates
- CORS-enabled for frontend integration
- Comprehensive error handling

## 🧪 Testing & Validation

### API Testing
```bash
# Run the test suite
python test_api.py

# Test specific endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/containers
```

### Example Usage
```python
# Start the system
from app.ingestion.watcher import docker_watcher
await docker_watcher.start()

# Query logs
from app.rag.retriever import rag_retriever
results = await rag_retriever.retrieve_context(
    container_id="my_container",
    question="What errors occurred?",
    k=8
)
```

## 🔍 Configuration Options

### Log Processing
```python
chunk_config = {
    "max_chunk_size": 1500,    # Maximum characters
    "min_chunk_size": 200,     # Minimum characters
    "max_lines": 25,           # Maximum lines
    "timeout_seconds": 30,     # Timeout for chunking
    "overlap_chars": 200       # Character overlap
}
```

### RAG Pipeline
```python
retriever_config = {
    "use_reranking": True,
    "initial_k": 20,           # Candidates for reranking
    "final_k": 8               # Final results
}
```

### Vector Store
```python
collections = {
    "main": "flat",      # Exact similarity
    "fast": "ann",       # Approximate search
    "error": "flat"      # Error analysis
}
```

## 📈 Performance & Monitoring

### System Statistics
- Container monitoring statistics
- Log processing metrics
- Query performance tracking
- Error rates and recovery

### Optimization Features
- Asynchronous processing
- Batch embedding generation
- Intelligent caching
- Resource usage monitoring

## 🚨 Troubleshooting

### Common Issues
1. **Docker Connection**: Ensure Docker daemon is running
2. **API Keys**: Verify Voyage AI and Gemini API keys are set
3. **Port Conflicts**: Check if port 8000 is available
4. **Permissions**: Ensure Docker socket access

### Debug Mode
```bash
# Run with debug logging
uvicorn app.main:app --log-level debug

# Check system status
curl http://localhost:8000/health
```

## 🔮 Future Enhancements

- Multi-modal log analysis
- Advanced semantic chunking
- Real-time analytics dashboard
- Federated search across containers
- Additional AI model integrations

## 📝 License

This project is part of the Dockerative Extension system. 