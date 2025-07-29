"""
Enhanced ChromaDB vector store for log chunks with comprehensive metadata and multiple indexing strategies.
Reference: https://docs.trychroma.com/
"""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)


class LogChunk(BaseModel):
    """Enhanced model for log chunk data with comprehensive metadata."""
    text: str
    container_id: str
    container_name: str
    timestamp: str
    chunk_id: str
    chunk_index: int
    total_chunks: int
    metadata: Dict[str, Any] = {}
    
    # Container metadata
    container_status: str = "unknown"
    container_image: str = ""
    container_created: str = ""
    container_started: str = ""
    
    # Chunk metadata
    line_count: int = 0
    char_count: int = 0
    log_level: str = "info"  # error, warn, info, debug
    source: str = "docker_logs"
    
    # Enhanced metadata for better search
    log_type: str = "general"  # error, warning, info, debug, system, application
    severity_score: float = 0.0  # 0.0 to 1.0 for error severity
    has_error: bool = False
    has_warning: bool = False
    error_count: int = 0
    warning_count: int = 0


class EnhancedVectorStore:
    """Enhanced ChromaDB vector store with multiple indexing strategies."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client and collections with enhanced schema."""
        logger.info(f"🗄️  Initializing Enhanced Vector Store with directory: {persist_directory}")
        
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        logger.info(f"📁 Created/verified directory: {persist_directory}")
        
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("✅ ChromaDB client initialized successfully")
            
            # Initialize collections with different indexing strategies
            self._init_collections()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {str(e)}")
            raise
    
    def _init_collections(self):
        """Initialize collections with different indexing strategies."""
        logger.info("📚 Initializing collections with enhanced schema...")
        
        # Main collection with comprehensive metadata
        self.main_collection = self.client.get_or_create_collection(
            name="docker_logs_main",
            metadata={
                "description": "Main Docker log chunks with comprehensive metadata",
                "created_at": datetime.now().isoformat(),
                "version": "3.0",
                "indexing": "flat"  # Flat indexing for exact similarity
            }
        )
        logger.info("📚 Main collection 'docker_logs_main' ready")
        
        # Fast collection with ANN indexing for approximate search
        self.fast_collection = self.client.get_or_create_collection(
            name="docker_logs_fast",
            metadata={
                "description": "Fast Docker log chunks with ANN indexing",
                "created_at": datetime.now().isoformat(),
                "version": "3.0",
                "indexing": "ann"  # Approximate nearest neighbor
            }
        )
        logger.info("📚 Fast collection 'docker_logs_fast' ready")
        
        # Error-focused collection for error analysis
        self.error_collection = self.client.get_or_create_collection(
            name="docker_logs_errors",
            metadata={
                "description": "Error-focused log chunks for error analysis",
                "created_at": datetime.now().isoformat(),
                "version": "3.0",
                "indexing": "flat"
            }
        )
        logger.info("📚 Error collection 'docker_logs_errors' ready")
    
    def _enhance_metadata(self, chunk: LogChunk) -> Dict[str, Any]:
        """Enhance metadata with additional searchable fields."""
        # Calculate severity score based on log level
        severity_map = {
            "error": 1.0,
            "warn": 0.7,
            "info": 0.3,
            "debug": 0.1
        }
        severity_score = severity_map.get(chunk.log_level, 0.3)
        
        # Count errors and warnings in text
        error_count = chunk.text.lower().count("error") + chunk.text.lower().count("exception")
        warning_count = chunk.text.lower().count("warn") + chunk.text.lower().count("warning")
        
        # Determine log type
        log_type = "general"
        if error_count > 0:
            log_type = "error"
        elif warning_count > 0:
            log_type = "warning"
        elif "debug" in chunk.text.lower():
            log_type = "debug"
        elif "system" in chunk.text.lower():
            log_type = "system"
        
        enhanced_metadata = {
            "container_id": chunk.container_id,
            "container_name": chunk.container_name,
            "container_status": chunk.container_status,
            "container_image": chunk.container_image,
            "container_created": chunk.container_created,
            "container_started": chunk.container_started,
            "timestamp": chunk.timestamp,
            "chunk_index": chunk.chunk_index,
            "total_chunks": chunk.total_chunks,
            "line_count": chunk.line_count,
            "char_count": chunk.char_count,
            "log_level": chunk.log_level,
            "source": chunk.source,
            "log_type": log_type,
            "severity_score": severity_score,
            "has_error": error_count > 0,
            "has_warning": warning_count > 0,
            "error_count": error_count,
            "warning_count": warning_count,
            **chunk.metadata
        }
        
        return enhanced_metadata
    
    async def upsert_chunks(self, chunks: List[LogChunk], embeddings: List[List[float]]):
        """
        Upsert log chunks with their embeddings to multiple collections.
        
        Args:
            chunks: List of log chunks
            embeddings: List of embedding vectors
        """
        logger.info(f"💾 Upserting {len(chunks)} chunks to multiple collections")
        
        try:
            # Prepare data for all collections
            ids = [chunk.chunk_id for chunk in chunks]
            texts = [chunk.text for chunk in chunks]
            metadatas = [self._enhance_metadata(chunk) for chunk in chunks]
            
            # Upsert to main collection (flat indexing)
            logger.info("📝 Upserting to main collection...")
            self.main_collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            # Upsert to fast collection (ANN indexing)
            logger.info("📝 Upserting to fast collection...")
            self.fast_collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            # Upsert error chunks to error collection
            error_chunks = []
            error_embeddings = []
            error_metadatas = []
            error_ids = []
            
            for i, chunk in enumerate(chunks):
                if chunk.log_level == "error" or "error" in chunk.text.lower():
                    error_chunks.append(chunk)
                    error_embeddings.append(embeddings[i])
                    error_metadatas.append(metadatas[i])
                    error_ids.append(ids[i])
            
            if error_chunks:
                logger.info(f"📝 Upserting {len(error_chunks)} error chunks to error collection...")
                self.error_collection.upsert(
                    ids=error_ids,
                    embeddings=error_embeddings,
                    documents=[chunk.text for chunk in error_chunks],
                    metadatas=error_metadatas
                )
            
            logger.info(f"✅ Successfully upserted {len(chunks)} chunks to all collections")
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert chunks: {str(e)}")
            raise Exception(f"Failed to upsert chunks: {str(e)}")
    
    async def query_similar(
        self, 
        query_embedding: List[float], 
        container_id: Optional[str] = None,
        k: int = 8,
        use_fast_index: bool = False,
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar log chunks with enhanced filtering.
        
        Args:
            query_embedding: Query embedding vector
            container_id: Optional container ID to search within
            k: Number of results to return
            use_fast_index: Whether to use fast ANN collection
            log_level: Optional log level filter
            
        Returns:
            List of similar documents with metadata
        """
        logger.info(f"🔍 Querying vector store")
        if container_id:
            logger.info(f"🎯 Filtering by container: {container_id}")
        if log_level:
            logger.info(f"🎯 Filtering by log level: {log_level}")
        logger.info(f"📊 Using {'fast' if use_fast_index else 'main'} collection")
        logger.info(f"🎯 Requesting top {k} results")
        
        try:
            # Choose collection based on indexing strategy
            collection = self.fast_collection if use_fast_index else self.main_collection
            
            # Build query parameters
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": k
            }
            
            # Build where clause for filtering
            where_clause = {}
            if container_id:
                where_clause["container_id"] = container_id
            if log_level:
                where_clause["log_level"] = log_level
            
            if where_clause:
                query_params["where"] = where_clause
            
            results = collection.query(**query_params)
            
            logger.info(f"📚 Collection returned {len(results['documents'][0])} results")
            
            # Format results
            documents = []
            for i in range(len(results["documents"][0])):
                doc = {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                }
                documents.append(doc)
            
            logger.info(f"✅ Query completed - Found {len(documents)} similar documents")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Failed to query similar chunks: {str(e)}")
            raise Exception(f"Failed to query similar chunks: {str(e)}")
    
    async def query_errors(
        self, 
        query_embedding: List[float], 
        container_id: Optional[str] = None,
        k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Query specifically for error logs.
        
        Args:
            query_embedding: Query embedding vector
            container_id: Optional container ID to search within
            k: Number of results to return
            
        Returns:
            List of error documents with metadata
        """
        logger.info(f"🔍 Querying error collection")
        
        try:
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": k
            }
            
            if container_id:
                query_params["where"] = {"container_id": container_id}
            
            results = self.error_collection.query(**query_params)
            
            logger.info(f"📚 Error collection returned {len(results['documents'][0])} results")
            
            # Format results
            documents = []
            for i in range(len(results["documents"][0])):
                doc = {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ Failed to query errors: {str(e)}")
            raise Exception(f"Failed to query errors: {str(e)}")
    
    async def get_container_logs(
        self, 
        container_id: str, 
        limit: int = 100,
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all log chunks for a specific container with optional filtering.
        
        Args:
            container_id: Container ID to get logs for
            limit: Maximum number of chunks to return
            log_level: Optional log level filter
            
        Returns:
            List of log chunks with metadata
        """
        logger.info(f"📋 Getting logs for container: {container_id}")
        
        try:
            where_clause = {"container_id": container_id}
            if log_level:
                where_clause["log_level"] = log_level
            
            results = self.main_collection.get(
                where=where_clause,
                limit=limit
            )
            
            logger.info(f"📄 Found {len(results['ids'])} chunks for container {container_id}")
            
            # Format results
            documents = []
            for i in range(len(results["ids"])):
                doc = {
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "id": results["ids"][i]
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ Failed to get container logs: {str(e)}")
            raise Exception(f"Failed to get container logs: {str(e)}")
    
    async def delete_container_logs(self, container_id: str):
        """
        Delete all log chunks for a specific container from all collections.
        
        Args:
            container_id: Container ID to delete logs for
        """
        logger.info(f"🗑️  Deleting all logs for container: {container_id}")
        
        try:
            collections = [self.main_collection, self.fast_collection, self.error_collection]
            
            for collection in collections:
                # Get all documents for the container
                results = collection.get(where={"container_id": container_id})
                
                if results["ids"]:
                    logger.info(f"📄 Found {len(results['ids'])} chunks to delete from {collection.name}")
                    collection.delete(ids=results["ids"])
                    logger.info(f"✅ Deleted {len(results['ids'])} chunks from {collection.name}")
                else:
                    logger.info(f"ℹ️  No chunks found for container {container_id} in {collection.name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to delete container logs: {str(e)}")
            raise Exception(f"Failed to delete container logs: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive collection statistics."""
        logger.info("📊 Getting enhanced vector store statistics")
        
        try:
            stats = {
                "main_collection": {
                    "name": "docker_logs_main",
                    "count": self.main_collection.count(),
                    "indexing": "flat"
                },
                "fast_collection": {
                    "name": "docker_logs_fast", 
                    "count": self.fast_collection.count(),
                    "indexing": "ann"
                },
                "error_collection": {
                    "name": "docker_logs_errors",
                    "count": self.error_collection.count(),
                    "indexing": "flat"
                }
            }
            
            # Get unique containers
            try:
                all_results = self.main_collection.get(limit=10000)
                containers = set()
                for metadata in all_results["metadatas"]:
                    if "container_id" in metadata:
                        containers.add(metadata["container_id"])
                
                stats["unique_containers"] = len(containers)
                
            except Exception as e:
                logger.warning(f"⚠️  Could not get detailed stats: {str(e)}")
            
            logger.info(f"📊 Enhanced stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {str(e)}")
            return {"error": str(e)}


# Global enhanced vector store instance
vector_store = EnhancedVectorStore() 