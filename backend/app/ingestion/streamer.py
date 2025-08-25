"""
Log streamer for tailing Docker logs with intelligent chunking and continuous streaming.
"""
import asyncio
# Set up logging
import logging
import re
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import docker
from app.rag.llm_client import llm_client
from app.storage.vector_store import LogChunk, vector_store
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class LogStreamer:
    """Log streamer with intelligent chunking and continuous streaming."""
    
    def __init__(self, container_id: str):
        """Initialize log streamer for a container."""
        self.container_id = container_id
        self.client = docker.from_env()
        self.container = self.client.containers.get(container_id)
        self.running = False
        self.buffer = []
        self.chunk_counter = 0
        self.last_processed_time = time.time()
        self.stream_start_time = None
        
        # Enhanced chunking configuration
        self.chunk_config = {
            "max_chunk_size": 1500,  # Maximum characters per chunk
            "min_chunk_size": 200,   # Minimum characters per chunk
            "max_lines": 25,          # Maximum lines per chunk
            "timeout_seconds": 30,    # Timeout for chunking
            "overlap_chars": 200      # Character overlap between chunks
        }
        
        # Initialize enhanced text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_config["max_chunk_size"],
            chunk_overlap=self.chunk_config["overlap_chars"],
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Prefer splitting on newlines
        )
        
        # Enhanced log level detection patterns
        self.log_patterns = {
            'error': re.compile(r'\b(error|ERROR|Error|exception|Exception|fail|Fail|FAIL|critical|Critical|CRITICAL)\b'),
            'warn': re.compile(r'\b(warn|WARN|Warn|warning|Warning|WARNING|deprecated|Deprecated)\b'),
            'debug': re.compile(r'\b(debug|DEBUG|Debug|trace|Trace|TRACE|verbose|Verbose)\b'),
            'info': re.compile(r'\b(info|INFO|Info|log|Log|LOG|notice|Notice)\b')
        }
        
        # Performance tracking
        self.stats = {
            "total_lines_processed": 0,
            "total_chunks_created": 0,
            "total_embeddings_generated": 0,
            "last_chunk_time": None,
            "processing_errors": 0
        }
        
    async def start_streaming(self):
        """Start continuous streaming from the container."""
        self.running = True
        self.stream_start_time = time.time()
        
        logger.info(f"📝 Starting log streaming for container: {self.container_id}")
        logger.info(f"📊 Chunk config: {self.chunk_config}")
        
        try:
            # Start background tasks
            streaming_task = asyncio.create_task(self._stream_logs())
            chunking_task = asyncio.create_task(self._periodic_chunking())
            
            # Wait for streaming to complete
            await streaming_task
            
            # Cancel chunking task
            chunking_task.cancel()
            try:
                await chunking_task
            except asyncio.CancelledError:
                pass
                
        except Exception as e:
            logger.error(f"❌ Error in enhanced streaming for container {self.container_id}: {str(e)}")
            self.stats["processing_errors"] += 1
        finally:
            self.running = False
            await self._finalize_streaming()
    
    async def _stream_logs(self):
        """Cntinuous log streaming with better error handling."""
        try:
            logs = self.container.logs(
                stream=True,
                timestamps=True,
                tail=0,  # Start from current time
                follow=True  # Continue following
            )
            
            logger.info(f"📡 Started log stream for container: {self.container_id}")
            
            for log_line in logs:
                if not self.running:
                    break
                    
                try:
                    # Decode and process log line
                    log_text = log_line.decode('utf-8').strip()
                    if log_text:
                        await self.process_log_line(log_text)
                        self.stats["total_lines_processed"] += 1
                        
                except UnicodeDecodeError as e:
                    logger.warning(f"⚠️ Unicode decode error for container {self.container_id}: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error processing log line for container {self.container_id}: {str(e)}")
                    self.stats["processing_errors"] += 1
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in log stream for container {self.container_id}: {str(e)}")
            self.stats["processing_errors"] += 1
    
    async def _periodic_chunking(self):
        """Periodic chunking to ensure timely processing."""
        while self.running:
            try:
                await asyncio.sleep(self.chunk_config["timeout_seconds"])
                
                if self.buffer and self.should_chunk():
                    await self.chunk_and_store()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in periodic chunking: {str(e)}")
                self.stats["processing_errors"] += 1
    
    async def process_log_line(self, log_line: str):
        """Process a single log line with enhanced analysis."""
        try:
            # Add to buffer
            self.buffer.append(log_line)
            
            # Check if buffer is ready for chunking
            if self.should_chunk():
                await self.chunk_and_store()
                
        except Exception as e:
            logger.error(f"❌ Error processing log line for container {self.container_id}: {str(e)}")
            self.stats["processing_errors"] += 1
    
    def should_chunk(self) -> bool:
        """Chunking decision logic."""
        if not self.buffer:
            return False
            
        # Check character count
        total_chars = sum(len(line) for line in self.buffer)
        if total_chars >= self.chunk_config["max_chunk_size"]:
            return True
            
        # Check line count
        if len(self.buffer) >= self.chunk_config["max_lines"]:
            return True
            
        # Check time since last chunk
        time_since_last = time.time() - self.last_processed_time
        if time_since_last >= self.chunk_config["timeout_seconds"] and total_chars >= self.chunk_config["min_chunk_size"]:
            return True
            
        return False
    
    def detect_log_level(self, text: str) -> str:
        """Log level detection with confidence scoring."""
        text_lower = text.lower()
        
        # Count pattern matches
        level_counts = {}
        for level, pattern in self.log_patterns.items():
            matches = len(pattern.findall(text_lower))
            level_counts[level] = matches
        
        # Determine primary level
        if level_counts.get('error', 0) > 0:
            return "error"
        elif level_counts.get('warn', 0) > 0:
            return "warn"
        elif level_counts.get('debug', 0) > 0:
            return "debug"
        else:
            return "info"
    
    async def get_container_metadata(self) -> Dict[str, Any]:
        """Get comprehensive container metadata with error handling."""
        try:
            # Reload container to get latest info
            await asyncio.to_thread(self.container.reload)
            
            # Get detailed container info
            container_info = self.container.attrs
            
            return {
                "container_name": self.container.name,
                "container_status": self.container.status,
                "container_image": self.container.image.tags[0] if self.container.image.tags else "unknown",
                "container_created": container_info.get('Created', ''),
                "container_started": container_info.get('State', {}).get('StartedAt', ''),
                "container_ports": container_info.get('NetworkSettings', {}).get('Ports', {}),
                "container_env": container_info.get('Config', {}).get('Env', []),
                "container_command": container_info.get('Config', {}).get('Cmd', []),
                "container_working_dir": container_info.get('Config', {}).get('WorkingDir', ''),
                "container_user": container_info.get('Config', {}).get('User', ''),
                "container_volumes": container_info.get('Mounts', []),
                "container_networks": list(container_info.get('NetworkSettings', {}).get('Networks', {}).keys())
            }
        except Exception as e:
            logger.error(f"Could not get container metadata: {str(e)}")
            return {
                "container_name": "unknown",
                "container_status": "unknown",
                "container_image": "unknown",
                "container_created": "",
                "container_started": "",
                "container_ports": {},
                "container_env": [],
                "container_command": [],
                "container_working_dir": "",
                "container_user": "",
                "container_volumes": [],
                "container_networks": []
            }
    
    async def chunk_and_store(self):
        """Chunking and storage with better error handling."""
        if not self.buffer:
            return
            
        try:
            # Combine buffer into text
            full_text = "\n".join(self.buffer)
            
            # Use intelligent text splitting
            text_chunks = self.text_splitter.split_text(full_text)
            
            logger.info(f"📝 Created {len(text_chunks)} chunks from {len(self.buffer)} log lines")
            
            # Get container metadata
            container_metadata = await self.get_container_metadata()
            
            # Create enhanced LogChunk objects
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk_id = f"{self.container_id}_{uuid.uuid4().hex[:8]}"
                timestamp = datetime.now().isoformat()
                
                # Detect log level for this chunk
                log_level = self.detect_log_level(chunk_text)
                
                # Calculate enhanced metadata
                error_count = chunk_text.lower().count("error") + chunk_text.lower().count("exception")
                warning_count = chunk_text.lower().count("warn") + chunk_text.lower().count("warning")
                
                chunk = LogChunk(
                    text=chunk_text,
                    container_id=self.container_id,
                    container_name=container_metadata["container_name"],
                    timestamp=timestamp,
                    chunk_id=chunk_id,
                    chunk_index=self.chunk_counter + i,
                    total_chunks=len(text_chunks),
                    line_count=chunk_text.count('\n') + 1,
                    char_count=len(chunk_text),
                    log_level=log_level,
                    container_status=container_metadata["container_status"],
                    container_image=container_metadata["container_image"],
                    container_created=container_metadata["container_created"],
                    container_started=container_metadata["container_started"],
                    has_error=error_count > 0,
                    has_warning=warning_count > 0,
                    error_count=error_count,
                    warning_count=warning_count,
                    metadata={
                        "original_line_count": len(self.buffer),
                        "chunk_method": "enhanced_recursive_splitter",
                        "container_ports": container_metadata.get("container_ports", {}),
                        "container_env": container_metadata.get("container_env", []),
                        "container_command": container_metadata.get("container_command", []),
                        "container_working_dir": container_metadata.get("container_working_dir", ""),
                        "container_user": container_metadata.get("container_user", ""),
                        "container_volumes": container_metadata.get("container_volumes", []),
                        "container_networks": container_metadata.get("container_networks", [])
                    }
                )
                chunks.append(chunk)
            
            # Generate embeddings using Voyage AI
            texts = [chunk.text for chunk in chunks]
            embeddings = await llm_client.embed_texts(texts)
            
            # Store in enhanced vector database
            await vector_store.upsert_chunks(chunks, embeddings)
            
            # Update statistics
            self.stats["total_chunks_created"] += len(chunks)
            self.stats["total_embeddings_generated"] += len(embeddings)
            self.stats["last_chunk_time"] = time.time()
            self.last_processed_time = time.time()
            
            logger.info(f"💾 Stored {len(chunks)} enhanced chunks for container {self.container_id}")
            
            # Update chunk counter
            self.chunk_counter += len(chunks)
            
            # Clear buffer
            self.buffer = []
            
        except Exception as e:
            logger.error(f"❌ Error chunking and storing logs for container {self.container_id}: {str(e)}")
            self.stats["processing_errors"] += 1
    
    async def stop_streaming(self):
        """Stop streaming and process remaining buffer."""
        self.running = False
        
        # Process remaining buffer
        if self.buffer:
            await self.chunk_and_store()
    
    async def _finalize_streaming(self):
        """Finalize streaming and log statistics."""
        duration = time.time() - self.stream_start_time if self.stream_start_time else 0
        
        logger.info(f"📊 Streaming statistics for container {self.container_id}:")
        logger.info(f"   ⏱️ Duration: {duration:.2f} seconds")
        logger.info(f"   📝 Lines processed: {self.stats['total_lines_processed']}")
        logger.info(f"   📄 Chunks created: {self.stats['total_chunks_created']}")
        logger.info(f"   🧠 Embeddings generated: {self.stats['total_embeddings_generated']}")
        logger.info(f"   ❌ Processing errors: {self.stats['processing_errors']}")
        
        if duration > 0:
            lines_per_second = self.stats['total_lines_processed'] / duration
            chunks_per_second = self.stats['total_chunks_created'] / duration
            logger.info(f"   📈 Lines per second: {lines_per_second:.2f}")
            logger.info(f"   📈 Chunks per second: {chunks_per_second:.2f}")
    
    async def get_container_status(self) -> str:
        """Get current container status."""
        try:
            # Run the blocking Docker operation in a thread
            await asyncio.to_thread(self.container.reload)
            return self.container.status
        except Exception:
            return "unknown"
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get current streaming statistics."""
        return {
            "container_id": self.container_id,
            "running": self.running,
            "buffer_size": len(self.buffer),
            "chunk_counter": self.chunk_counter,
            "stats": self.stats.copy(),
            "chunk_config": self.chunk_config.copy()
        } 