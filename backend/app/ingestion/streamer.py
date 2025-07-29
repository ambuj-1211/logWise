"""
Log streamer for tailing Docker logs, chunking, embedding, and upserting to vector store.
"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional

import docker
from app.rag.llm_client import llm_client
from app.storage.vector_store import LogChunk, vector_store


class LogStreamer:
    """Streams and processes Docker container logs."""
    
    def __init__(self, container_id: str):
        """Initialize log streamer for a container."""
        self.container_id = container_id
        self.client = docker.from_env()
        self.container = self.client.containers.get(container_id)
        self.running = False
        self.buffer = []
        self.buffer_size = 300  # Approximate tokens per chunk
        
    async def start_streaming(self):
        """Start streaming logs from the container."""
        self.running = True
        print(f"📝 Starting log streaming for container: {self.container_id}")
        
        try:
            # Run the blocking Docker logs operation in a thread
            await asyncio.to_thread(self._stream_logs)
            
        except Exception as e:
            print(f"❌ Error streaming logs for container {self.container_id}: {str(e)}")
        finally:
            self.running = False
            print(f"🛑 Stopped log streaming for container: {self.container_id}")
    
    def _stream_logs(self):
        """Stream logs in a blocking manner (runs in thread)."""
        try:
            # Get logs with timestamps
            logs = self.container.logs(
                stream=True,
                timestamps=True,
                tail=0  # Start from current time
            )
            
            for log_line in logs:
                if not self.running:
                    break
                    
                # Decode and process log line
                log_text = log_line.decode('utf-8').strip()
                if log_text:
                    # Schedule processing on the main event loop
                    asyncio.create_task(self.process_log_line(log_text))
                    
        except Exception as e:
            print(f"Error in log stream for container {self.container_id}: {str(e)}")
    
    async def process_log_line(self, log_line: str):
        """Process a single log line."""
        try:
            # Add to buffer
            self.buffer.append(log_line)
            
            # Check if buffer is ready for chunking
            if self.should_chunk():
                await self.chunk_and_store()
                
        except Exception as e:
            print(f"Error processing log line for container {self.container_id}: {str(e)}")
    
    def should_chunk(self) -> bool:
        """Check if buffer should be chunked."""
        # Simple heuristic: chunk when buffer has enough lines or characters
        total_chars = sum(len(line) for line in self.buffer)
        return len(self.buffer) >= 10 or total_chars >= self.buffer_size
    
    async def chunk_and_store(self):
        """Create chunks from buffer and store in vector database."""
        if not self.buffer:
            return
            
        try:
            # Create log chunks
            chunks = []
            chunk_text = "\n".join(self.buffer)
            chunk_id = f"{self.container_id}_{uuid.uuid4().hex[:8]}"
            timestamp = datetime.now().isoformat()
            
            chunk = LogChunk(
                text=chunk_text,
                container_id=self.container_id,
                timestamp=timestamp,
                chunk_id=chunk_id,
                metadata={
                    "line_count": len(self.buffer),
                    "container_name": self.container.name
                }
            )
            chunks.append(chunk)
            
            # Generate embeddings
            texts = [chunk.text for chunk in chunks]
            embeddings = await llm_client.embed_texts(texts)
            
            # Store in vector database
            await vector_store.upsert_chunks(chunks, embeddings)
            
            print(f"💾 Stored {len(chunks)} chunks for container {self.container_id}")
            
            # Clear buffer
            self.buffer = []
            
        except Exception as e:
            print(f"❌ Error chunking and storing logs for container {self.container_id}: {str(e)}")
    
    async def stop_streaming(self):
        """Stop streaming logs."""
        self.running = False
        
        # Process remaining buffer
        if self.buffer:
            await self.chunk_and_store()
    
    async def get_container_status(self) -> str:
        """Get current container status."""
        try:
            # Run the blocking Docker operation in a thread
            await asyncio.to_thread(self.container.reload)
            return self.container.status
        except Exception:
            return "unknown" 