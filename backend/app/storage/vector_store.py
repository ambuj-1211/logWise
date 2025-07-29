"""
ChromaDB vector store for log chunks with metadata.
Reference: https://docs.trychroma.com/
"""
import logging
import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)


class LogChunk(BaseModel):
    """Model for log chunk data."""
    text: str
    container_id: str
    timestamp: str
    chunk_id: str
    metadata: Dict[str, Any] = {}


class VectorStore:
    """ChromaDB vector store for log chunks."""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client and collection."""
        logger.info(f"🗄️  Initializing Vector Store with directory: {persist_directory}")
        
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
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="logs",
                metadata={"description": "Docker container log chunks"}
            )
            logger.info("📚 Collection 'logs' ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {str(e)}")
            raise
    
    async def upsert_chunks(self, chunks: List[LogChunk], embeddings: List[List[float]]):
        """
        Upsert log chunks with their embeddings.
        
        Args:
            chunks: List of log chunks
            embeddings: List of embedding vectors
        """
        logger.info(f"💾 Upserting {len(chunks)} chunks to vector store")
        
        try:
            # Prepare data for ChromaDB
            ids = [chunk.chunk_id for chunk in chunks]
            texts = [chunk.text for chunk in chunks]
            metadatas = [
                {
                    "container_id": chunk.container_id,
                    "timestamp": chunk.timestamp,
                    **chunk.metadata
                }
                for chunk in chunks
            ]
            
            logger.info(f"📝 Chunk details:")
            for i, chunk in enumerate(chunks):
                logger.info(f"   📄 Chunk {i+1}: {chunk.chunk_id}")
                logger.info(f"      🐳 Container: {chunk.container_id}")
                logger.info(f"      ⏰ Timestamp: {chunk.timestamp}")
                logger.info(f"      📏 Text length: {len(chunk.text)} characters")
                logger.info(f"      🧠 Embedding dimensions: {len(embeddings[i])}")
            
            # Upsert to ChromaDB
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info(f"✅ Successfully upserted {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert chunks: {str(e)}")
            raise Exception(f"Failed to upsert chunks: {str(e)}")
    
    async def query_similar(
        self, 
        query_embedding: List[float], 
        container_id: str, 
        k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Query for similar log chunks within a container.
        
        Args:
            query_embedding: Query embedding vector
            container_id: Container ID to search within
            k: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        logger.info(f"🔍 Querying vector store for container: {container_id}")
        logger.info(f"📊 Query embedding dimensions: {len(query_embedding)}")
        logger.info(f"🎯 Requesting top {k} results")
        
        try:
            # Log embedding stats
            logger.info(f"📈 Query embedding stats - Min: {min(query_embedding):.4f}, "
                       f"Max: {max(query_embedding):.4f}, "
                       f"Mean: {sum(query_embedding)/len(query_embedding):.4f}")
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where={"container_id": container_id}
            )
            
            logger.info(f"📚 ChromaDB returned {len(results['documents'][0])} results")
            
            # Format results
            documents = []
            for i in range(len(results["documents"][0])):
                doc = {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                }
                documents.append(doc)
                
                logger.info(f"📄 Result {i+1}:")
                logger.info(f"   📝 Text preview: {doc['text'][:100]}{'...' if len(doc['text']) > 100 else ''}")
                logger.info(f"   🏷️  Metadata: {doc['metadata']}")
                if doc.get('distance'):
                    logger.info(f"   📏 Distance: {doc['distance']:.4f}")
            
            logger.info(f"✅ Query completed - Found {len(documents)} similar documents")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Failed to query similar chunks: {str(e)}")
            raise Exception(f"Failed to query similar chunks: {str(e)}")
    
    async def delete_container_logs(self, container_id: str):
        """
        Delete all log chunks for a specific container.
        
        Args:
            container_id: Container ID to delete logs for
        """
        logger.info(f"🗑️  Deleting all logs for container: {container_id}")
        
        try:
            # Get all documents for the container
            results = self.collection.get(
                where={"container_id": container_id}
            )
            
            if results["ids"]:
                logger.info(f"📄 Found {len(results['ids'])} chunks to delete")
                self.collection.delete(ids=results["ids"])
                logger.info(f"✅ Deleted {len(results['ids'])} chunks for container {container_id}")
            else:
                logger.info(f"ℹ️  No chunks found for container {container_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to delete container logs: {str(e)}")
            raise Exception(f"Failed to delete container logs: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        logger.info("📊 Getting vector store statistics")
        
        try:
            count = self.collection.count()
            logger.info(f"📈 Total chunks in collection: {count}")
            
            stats = {
                "total_chunks": count,
                "collection_name": "logs"
            }
            
            logger.info(f"📊 Stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {str(e)}")
            return {"error": str(e)}


# Global vector store instance
vector_store = VectorStore() 