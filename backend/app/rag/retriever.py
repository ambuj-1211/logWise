"""
Enhanced RAG retriever with two-stage pipeline: vector similarity + reranking.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from app.rag.llm_client import llm_client
from app.storage.vector_store import vector_store

# Set up logging
logger = logging.getLogger(__name__)


class RAGRetriever:
    """Enhanced RAG retriever with two-stage retrieval pipeline."""
    
    def __init__(self):
        """Initialize the enhanced retriever."""
        self.use_reranking = True
        self.initial_k = 20  # Get more candidates for reranking
        self.final_k = 8     # Final number of results after reranking
        
    async def retrieve_context(
        self, 
        container_id: str, 
        question: str, 
        k: int = 8,
        use_fast_index: bool = False,
        use_reranking: bool = True,
        log_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced retrieval with two-stage pipeline: vector similarity + reranking.
        
        Args:
            container_id: Container ID to search within
            question: User question
            k: Number of final results to return
            use_fast_index: Whether to use fast ANN collection
            use_reranking: Whether to use reranking
            log_level: Optional log level filter
            
        Returns:
            List of relevant documents with text and metadata
        """
        logger.info(f"🔍 Starting enhanced RAG retrieval for container: {container_id}")
        logger.info(f"❓ Question: {question}")
        logger.info(f"📊 Using {'fast' if use_fast_index else 'main'} collection")
        logger.info(f"🔄 Reranking enabled: {use_reranking}")
        
        try:
            # Stage 1: Generate embedding for the question
            logger.info("🧠 Stage 1: Generating embedding for the question...")
            question_embeddings = await llm_client.embed_texts([question])
            question_embedding = question_embeddings[0]
            
            logger.info(f"✅ Question embedding generated - Dimensions: {len(question_embedding)}")
            
            # Stage 2: Vector similarity search
            logger.info("🔎 Stage 2: Vector similarity search...")
            initial_k = self.initial_k if use_reranking else k
            
            similar_docs = await vector_store.query_similar(
                query_embedding=question_embedding,
                container_id=container_id,
                k=initial_k,
                use_fast_index=use_fast_index,
                log_level=log_level
            )
            
            logger.info(f"📚 Found {len(similar_docs)} initial candidates")
            
            if not similar_docs:
                logger.warning("⚠️  No documents found in vector search")
                return []
            
            # Stage 3: Reranking (if enabled)
            if use_reranking and len(similar_docs) > 1:
                logger.info("🔄 Stage 3: Reranking documents...")
                reranked_docs = await self._rerank_documents(question, similar_docs, k)
                logger.info(f"✅ Reranking completed - Returning top {len(reranked_docs)} results")
                return reranked_docs
            else:
                # Return top k results without reranking
                final_docs = similar_docs[:k]
                logger.info(f"✅ Returning top {len(final_docs)} results without reranking")
                return final_docs
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve context: {str(e)}")
            raise Exception(f"Failed to retrieve context: {str(e)}")
    
    async def _rerank_documents(
        self, 
        question: str, 
        documents: List[Dict[str, Any]], 
        k: int
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using Voyage AI reranking.
        
        Args:
            question: User question
            documents: List of documents to rerank
            k: Number of top results to return
            
        Returns:
            Reranked list of documents
        """
        try:
            # Extract document texts for reranking
            doc_texts = [doc["text"] for doc in documents]
            
            # Use Voyage AI for reranking
            rerank_results = await llm_client.rerank_documents(
                query=question,
                documents=doc_texts,
                top_k=k
            )
            
            # Map reranked results back to original documents
            reranked_docs = []
            for result in rerank_results:
                original_index = result["index"]
                if original_index < len(documents):
                    doc = documents[original_index].copy()
                    doc["rerank_score"] = result["score"]
                    reranked_docs.append(doc)
            
            logger.info(f"🔄 Reranking completed - Top score: {rerank_results[0]['score']:.4f}")
            return reranked_docs
            
        except Exception as e:
            logger.error(f"❌ Failed to rerank documents: {str(e)}")
            # Fallback to original documents
            return documents[:k]
    
    async def retrieve_errors(
        self, 
        container_id: str, 
        question: str, 
        k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Retrieve error-specific context from error collection.
        
        Args:
            container_id: Container ID to search within
            question: User question
            k: Number of results to return
            
        Returns:
            List of error documents with metadata
        """
        logger.info(f"🔍 Retrieving error context for container: {container_id}")
        logger.info(f"❓ Question: {question}")
        
        try:
            # Generate embedding for the question
            question_embeddings = await llm_client.embed_texts([question])
            question_embedding = question_embeddings[0]
            
            # Query error collection
            error_docs = await vector_store.query_errors(
                query_embedding=question_embedding,
                container_id=container_id,
                k=k
            )
            
            logger.info(f"📚 Found {len(error_docs)} error documents")
            return error_docs
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve error context: {str(e)}")
            raise Exception(f"Failed to retrieve error context: {str(e)}")
    
    def build_prompt(self, docs: List[Dict[str, Any]], question: str) -> str:
        """
        Build an enhanced prompt from retrieved documents and question.
        
        Args:
            docs: Retrieved documents
            question: User question
            
        Returns:
            Formatted prompt for LLM
        """
        logger.info(f"🔨 Building enhanced prompt from {len(docs)} documents")
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            metadata = doc['metadata']
            timestamp = metadata.get('timestamp', 'unknown')
            log_level = metadata.get('log_level', 'info')
            container_name = metadata.get('container_name', 'unknown')
            
            # Add rerank score if available
            score_info = ""
            if 'rerank_score' in doc:
                score_info = f" (relevance: {doc['rerank_score']:.3f})"
            
            context_parts.append(
                f"Log {i} (timestamp: {timestamp}, level: {log_level}, container: {container_name}){score_info}:\n{doc['text']}"
            )
        
        context = "\n\n".join(context_parts)
        
        prompt = f"""You are an expert Docker log analyst. Analyze the following container logs and answer the user's question with specific references to log entries.

Log Context:
{context}

Question: {question}

Instructions:
1. Analyze the logs systematically, looking for patterns and issues
2. Provide specific timestamps and log entries when referencing information
3. If the logs contain errors, explain what went wrong and potential causes
4. If the information is not in the logs, say so clearly
5. Be concise but thorough in your analysis
6. Consider log levels (error, warn, info, debug) when analyzing severity
7. Be brief and to the point.
8. Take conversation gradually understand what the user wants and provide the insights from the logs.

Answer for the question according to the context provided:"""
        
        logger.info(f"📝 Built enhanced prompt - Total length: {len(prompt)} characters")
        logger.info(f"📄 Context length: {len(context)} characters")
        logger.info(f"❓ Question length: {len(question)} characters")
        
        return prompt
    
    def extract_references(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract enhanced reference information from retrieved documents.
        
        Args:
            docs: Retrieved documents
            
        Returns:
            List of reference information
        """
        logger.info(f"📋 Extracting enhanced references from {len(docs)} documents")
        
        references = []
        for i, doc in enumerate(docs, 1):
            metadata = doc["metadata"]
            ref = {
                "id": i,
                "timestamp": metadata.get("timestamp", "unknown"),
                "log_level": metadata.get("log_level", "info"),
                "container_name": metadata.get("container_name", "unknown"),
                "text_preview": doc["text"][:100] + "..." if len(doc["text"]) > 100 else doc["text"],
                "distance": doc.get("distance"),
                "rerank_score": doc.get("rerank_score"),
                "severity_score": metadata.get("severity_score", 0.0),
                "has_error": metadata.get("has_error", False),
                "has_warning": metadata.get("has_warning", False)
            }
            references.append(ref)
            
            logger.info(f"📄 Reference {i}: {ref['text_preview']}")
            logger.info(f"   🏷️  Level: {ref['log_level']}, Container: {ref['container_name']}")
            if ref.get('rerank_score'):
                logger.info(f"   📊 Rerank score: {ref['rerank_score']:.3f}")
        
        logger.info(f"✅ Extracted {len(references)} enhanced references")
        return references
    
    async def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval pipeline statistics."""
        logger.info("📊 Getting retrieval pipeline statistics")
        
        try:
            # Get vector store stats
            vector_stats = vector_store.get_stats()
            
            # Test LLM connections
            llm_stats = await llm_client.test_connections()
            
            stats = {
                "vector_store": vector_stats,
                "llm_connections": llm_stats,
                "retrieval_config": {
                    "use_reranking": self.use_reranking,
                    "initial_k": self.initial_k,
                    "final_k": self.final_k
                }
            }
            
            logger.info(f"📊 Retrieval stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get retrieval stats: {str(e)}")
            return {"error": str(e)}


# Global enhanced retriever instance
rag_retriever =     RAGRetriever() 