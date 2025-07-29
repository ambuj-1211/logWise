"""
RAG retriever for vector search and context retrieval.
"""
import logging
from typing import Any, Dict, List

from app.rag.llm_client import llm_client
from app.storage.vector_store import vector_store

# Set up logging
logger = logging.getLogger(__name__)


class RAGRetriever:
    """RAG retriever for log analysis."""
    
    async def retrieve_context(
        self, 
        container_id: str, 
        question: str, 
        k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a question about container logs.
        
        Args:
            container_id: Container ID to search within
            question: User question
            k: Number of similar chunks to retrieve
            
        Returns:
            List of relevant documents with text and metadata
        """
        logger.info(f"🔍 Starting RAG retrieval for container: {container_id}")
        logger.info(f"❓ Question: {question}")
        logger.info(f"📊 Retrieving top {k} similar chunks")
        
        try:
            # Generate embedding for the question
            logger.info("🧠 Generating embedding for the question...")
            question_embeddings = await llm_client.embed_texts([question])
            question_embedding = question_embeddings[0]
            
            logger.info(f"✅ Question embedding generated - Dimensions: {len(question_embedding)}")
            
            # Query vector store for similar chunks
            logger.info("🔎 Querying vector store for similar chunks...")
            similar_docs = await vector_store.query_similar(
                query_embedding=question_embedding,
                container_id=container_id,
                k=k
            )
            
            logger.info(f"📚 Found {len(similar_docs)} similar documents")
            
            # Log details about retrieved documents
            for i, doc in enumerate(similar_docs):
                logger.info(f"📄 Document {i+1}:")
                logger.info(f"   📝 Text preview: {doc['text'][:100]}{'...' if len(doc['text']) > 100 else ''}")
                logger.info(f"   🏷️  Metadata: {doc['metadata']}")
                if 'distance' in doc:
                    logger.info(f"   📏 Distance: {doc['distance']:.4f}")
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve context: {str(e)}")
            raise Exception(f"Failed to retrieve context: {str(e)}")
    
    def build_prompt(self, docs: List[Dict[str, Any]], question: str) -> str:
        """
        Build a prompt from retrieved documents and question.
        
        Args:
            docs: Retrieved documents
            question: User question
            
        Returns:
            Formatted prompt for LLM
        """
        logger.info(f"🔨 Building prompt from {len(docs)} documents")
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            timestamp = doc['metadata'].get('timestamp', 'unknown')
            context_parts.append(f"Log {i} (timestamp: {timestamp}):\n{doc['text']}")
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""You are a helpful assistant for analyzing Docker container logs. Answer the following question based only on the provided log context.

Log Context:
{context}

Question: {question}

Instructions:
1. Analyze the logs step-by-step
2. Provide specific references to log entries when possible
3. If the information is not in the logs, say so clearly
4. Be concise but thorough in your analysis

Answer:"""
        
        logger.info(f"📝 Built prompt - Total length: {len(prompt)} characters")
        logger.info(f"📄 Context length: {len(context)} characters")
        logger.info(f"❓ Question length: {len(question)} characters")
        
        return prompt
    
    def extract_references(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract reference information from retrieved documents.
        
        Args:
            docs: Retrieved documents
            
        Returns:
            List of reference information
        """
        logger.info(f"📋 Extracting references from {len(docs)} documents")
        
        references = []
        for i, doc in enumerate(docs, 1):
            ref = {
                "id": i,
                "timestamp": doc["metadata"].get("timestamp", "unknown"),
                "text_preview": doc["text"][:100] + "..." if len(doc["text"]) > 100 else doc["text"],
                "distance": doc.get("distance")
            }
            references.append(ref)
            
            logger.info(f"📄 Reference {i}: {ref['text_preview']}")
        
        logger.info(f"✅ Extracted {len(references)} references")
        return references


# Global retriever instance
rag_retriever = RAGRetriever() 