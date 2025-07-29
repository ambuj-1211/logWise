"""
API routes for RAG-based log querying.
"""
import logging
from typing import Any, Dict, List

from app.rag.llm_client import llm_client
from app.rag.retriever import rag_retriever
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    """Query request model."""
    container_id: str
    question: str
    k: int = 8


class QueryResponse(BaseModel):
    """Query response model."""
    answer: str
    references: List[Dict[str, Any]]
    container_id: str
    question: str


@router.post("/api/logs/query", response_model=QueryResponse)
async def query_logs(request: QueryRequest) -> QueryResponse:
    """
    Query container logs using RAG.
    
    Args:
        request: Query request with container_id and question
        
    Returns:
        QueryResponse with answer and references
    """
    logger.info("🚀 Starting RAG query request")
    logger.info(f"📦 Request details:")
    logger.info(f"   🐳 Container ID: {request.container_id}")
    logger.info(f"   ❓ Question: {request.question}")
    logger.info(f"   📊 Top-k: {request.k}")
    
    try:
        # Step 1: Retrieve relevant context
        logger.info("🔍 Step 1: Retrieving relevant context...")
        docs = await rag_retriever.retrieve_context(
            container_id=request.container_id,
            question=request.question,
            k=request.k
        )
        
        if not docs:
            logger.warning("⚠️  No relevant documents found")
            return QueryResponse(
                answer="No relevant log data found for this question. The container might not have any logs or the question doesn't match the available log content.",
                references=[],
                container_id=request.container_id,
                question=request.question
            )
        
        logger.info(f"✅ Retrieved {len(docs)} relevant documents")
        
        # Step 2: Build prompt from retrieved documents
        logger.info("🔨 Step 2: Building prompt from retrieved documents...")
        prompt = rag_retriever.build_prompt(docs, request.question)
        
        # Step 3: Generate answer using LLM
        logger.info("🤖 Step 3: Generating answer using LLM...")
        answer = await llm_client.generate_answer(prompt)
        
        # Step 4: Extract references
        logger.info("📋 Step 4: Extracting references...")
        references = rag_retriever.extract_references(docs)
        
        logger.info("✅ RAG query completed successfully")
        logger.info(f"📝 Answer length: {len(answer)} characters")
        logger.info(f"📄 Number of references: {len(references)}")
        
        return QueryResponse(
            answer=answer,
            references=references,
            container_id=request.container_id,
            question=request.question
        )
        
    except Exception as e:
        logger.error(f"❌ RAG query failed: {str(e)}")
        logger.error(f"🔍 Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/api/logs/query/suggestions")
async def get_query_suggestions(container_id: str = None) -> List[str]:
    """Get suggested questions for a container."""
    logger.info(f"💡 Getting query suggestions for container: {container_id}")
    
    suggestions = [
        "What errors occurred in the logs?",
        "Show me the startup sequence",
        "What are the most recent log entries?",
        "Are there any warning messages?",
        "What processes are running?",
        "Show me network-related logs",
        "What configuration changes were made?",
        "Are there any performance issues?"
    ]
    
    logger.info(f"✅ Returning {len(suggestions)} query suggestions")
    return suggestions


@router.get("/api/logs/query/stats")
async def get_query_stats(container_id: str = None):
    """Get query statistics for a container."""
    logger.info(f"📊 Getting query stats for container: {container_id}")
    
    try:
        from app.storage.vector_store import vector_store

        # Get vector store stats
        stats = vector_store.get_stats()
        logger.info(f"📈 Vector store stats: {stats}")
        
        return {
            "container_id": container_id,
            "vector_store": stats,
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get query stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get query stats: {str(e)}"
        ) 