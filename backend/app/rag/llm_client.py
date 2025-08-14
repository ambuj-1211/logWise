"""
Enhanced LLM client supporting Google Gemini for chat and Voyage AI for embeddings and reranking.
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import voyageai
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class LLMClient:
    """Enhanced LLM client with Gemini for chat and Voyage AI for embeddings/reranking."""
    
    def __init__(self):
        """Initialize both Gemini and Voyage AI clients."""
        logger.info("🤖 Initializing Enhanced LLM Client...")
        
        # Initialize Gemini for chat
        self._init_gemini()
        
        # Initialize Voyage AI for embeddings and reranking
        self._init_voyage()
        
        logger.info("✅ Enhanced LLM Client initialized successfully")
    
    def _init_gemini(self):
        """Initialize Google Gemini client for chat completions."""
        logger.info("🔑 Initializing Gemini client...")
        
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("⚠️  GEMINI_API_KEY not found - Gemini chat will be disabled")
            self.gemini_available = False
            return
        
        try:
            # Configure Gemini
            client = genai.Client(api_key)
            # Initialize models
            self.client = client
            self.completion_model = "gemini-2.5-flash"
            self.gemini_available = True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini: {str(e)}")
            self.gemini_available = False
    
    def _init_voyage(self):
        """Initialize Voyage AI client for embeddings and reranking."""
        logger.info("🚢 Initializing Voyage AI client...")
        
        # Get API key from environment
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise ValueError("VOYAGE_API_KEY not found in environment variables")
        
        try:
            # Initialize Voyage AI client
            self.voyage_client = voyageai.Client(api_key=api_key)
            
            # Set default embedding model
            self.embedding_model = "voyage-3"  # Best for general purpose
            self.rerank_model = "rerank-2.5"  # Best for reranking
            
            logger.info("✅ Voyage AI client initialized successfully")
            logger.info(f"🧠 Embedding model: {self.embedding_model}")
            logger.info(f"🔄 Rerank model: {self.rerank_model}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Voyage AI: {str(e)}")
            raise Exception(f"Failed to initialize Voyage AI: {str(e)}")
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Voyage AI.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"🧠 Generating embeddings for {len(texts)} texts using Voyage AI")
        
        try:
            # Use Voyage AI for embeddings
            embeddings = self.voyage_client.embed(
                texts=texts,
                model=self.embedding_model,
                input_type="document"
            )
            
            logger.info(f"✅ Successfully generated {len(embeddings)} embeddings")
            logger.info(f"📊 Embedding dimensions: {len(embeddings[0]) if embeddings else 0}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings: {str(e)}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")
    
    async def rerank_documents(
        self, 
        query: str, 
        documents: List[str], 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using Voyage AI reranking.
        
        Args:
            query: Search query
            documents: List of documents to rerank
            top_k: Number of top results to return
            
        Returns:
            List of reranked documents with scores
        """
        logger.info(f"🔄 Reranking {len(documents)} documents for query: {query[:100]}...")
        
        try:
            # Use Voyage AI for reranking
            rerank_results = self.voyage_client.rerank(
                query=query,
                documents=documents,
                model=self.rerank_model,
                top_k=top_k
            )
            
            # Format results
            results = []
            for result in rerank_results:
                results.append({
                    "text": result.document,
                    "score": result.relevance_score,
                    "index": result.index
                })
            
            logger.info(f"✅ Reranking completed - Top score: {results[0]['score']:.4f}")
            return results
            
        except Exception as e:
            raise Exception(f"Failed to rerank documents: {str(e)}")
    
    async def generate_answer(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate completion using Gemini.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        if not self.gemini_available:
            raise Exception("Gemini is not available - check GEMINI_API_KEY")
        
        logger.info(f"🤖 Generating completion with prompt length: {len(prompt)}")
        logger.info(f"📝 Prompt preview: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
        
        try:
            
            # Generate completion
            response = self.client.models.generate_content(
                model=self.completion_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=max_tokens
                )
            )
            answer = response.text
            
            logger.info(f"✅ Completion generated successfully!")
            logger.info(f"💬 Response length: {len(answer)} characters")
            logger.info(f"📝 Response preview: {answer[:200]}{'...' if len(answer) > 200 else ''}")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Failed to generate completion: {str(e)}")
            raise Exception(f"Failed to generate completion: {str(e)}")
    
    async def test_connections(self) -> Dict[str, bool]:
        """Test both Gemini and Voyage AI connections."""
        logger.info("🧪 Testing LLM connections...")
        
        results = {
            "voyage_embeddings": False,
            "voyage_reranking": False,
            "gemini_chat": False
        }
        
        try:
            # Test Voyage AI embeddings
            test_text = "Hello, this is a test."
            embeddings = await self.embed_texts([test_text])
            if embeddings and len(embeddings[0]) > 0:
                results["voyage_embeddings"] = True
                logger.info("✅ Voyage AI embeddings test passed")
            
            # Test Voyage AI reranking
            test_docs = ["Document 1", "Document 2", "Document 3"]
            rerank_results = await self.rerank_documents("test query", test_docs, top_k=2)
            if rerank_results:
                results["voyage_reranking"] = True
                logger.info("✅ Voyage AI reranking test passed")
            
            # Test Gemini chat
            if self.gemini_available:
                test_prompt = "Say 'Hello, Gemini is working!'"
                response = await self.generate_answer(test_prompt, max_tokens=50)
                if response:
                    results["gemini_chat"] = True
                    logger.info("✅ Gemini chat test passed")
            
            logger.info(f"📊 Connection test results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return results


# Global enhanced LLM client instance
llm_client = LLMClient()
