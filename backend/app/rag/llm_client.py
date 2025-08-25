"""
Enhanced LLM client supporting Google OPENAI for chat and Voyage AI for embeddings and reranking.
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import openai
import voyageai
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class LLMClient:
    """Enhanced LLM client with OPENAI for chat and Voyage AI for embeddings/reranking."""
    
    def __init__(self):
        """Initialize both OPENAI and Voyage AI clients."""
        # Initialize OPENAI for chat
        self._init_openai()
        # Initialize Voyage AI for embeddings and reranking
        self._init_voyage()
        logger.info("LLM client initialized.")
    
    def _init_openai(self):
        """Initialize OPENAI client for chat completions."""
        logger.info("🔑 Initializing openai client...")
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️ OPENAI_API_KEY not found")
            self.openai_available = False
            return
        
        try:
            # Configure OPENAI
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Initialize models
            self.openai_client = client
            # self.completion_model = "gemini-2.5-flash"
            # self.gemini_available = True
            self.completion_model = "gpt-4.1-nano"
            self.openai_available = True
            
            
            
        except Exception as e:
            logger.error(f"Failed to initialize openai: {str(e)}")
            self.openai_available = False
    
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
            self.embedding_model = "voyage-3"
            self.rerank_model = "rerank-2.5"
            
            logger.info("✅ Voyage AI client initialized successfully")
            
        except Exception as e:
            raise Exception(f"Failed to initialize Voyage AI: {str(e)}")


    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Voyage AI.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        
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
            for result in rerank_results.results:
                results.append({
                    "text": result.document,
                    "score": result.relevance_score,
                    "index": result.index
                })
            
            logger.info(f"✅ Reranking completed - Top score: {results[0]['score']:.4f}")
            # total_tokens is the parameter in the rerank_results to get the total tokens of the string
            logger.info(f"Total tokens are {rerank_results.total_tokens}")
            return results
            
        except Exception as e:
            raise Exception(f"Failed to rerank documents: {str(e)}")
    
    async def generate_answer(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate completion using OPENAI.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        if not self.openai_available:
            raise Exception("OPENAI is not available - check OPENAI_API_KEY")
        
        logger.info(f"🤖 Generating completion with prompt length: {len(prompt)}")
        logger.info(f"📝 Prompt preview: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
        
        try:
            
            # Generate completion
            # response = self.gemini_client.models.generate_content(
            #     model=self.completion_model,
            #     contents=prompt,
            #     config=types.GenerateContentConfig(
            #         temperature=0.1,
            #         max_output_tokens=max_tokens
            #     )
            # )
            # Generate Completion
            response = self.openai_client.chat.completions.create(
            model=self.completion_model,
            # messages=[
            #     {"role": "system", "content": "You are an expert at extracting numerical requirements from job postings. Always return only the number as a float or 'null' if not specified."},
            #     {"role": "user", "content": prompt}
            # ],
            messages = [
                {"role": "system", "content": "Your task is to create a short answer according to the prompt given to you, Give Concise Answers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
            )
            
        
            answer = response.choices[0].message.content
            
            logger.info(f"✅ Completion generated successfully!")
            logger.info(f"💬 Response length: {len(answer)} characters")
            logger.info(f"📝 Response preview: {answer[:200]}{'...' if len(answer) > 200 else ''}")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Failed to generate completion: {str(e)}")
            raise Exception(f"Failed to generate completion: {str(e)}")
    
    async def test_connections(self) -> Dict[str, bool]:
        """Test both OPENAI and Voyage AI connections."""
        logger.info("🧪 Testing LLM connections...")
        
        results = {
            "voyage_embeddings": False,
            "voyage_reranking": False,
            "openai_chat": False
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
            
            # Test openai chat
            if self.openai_available:
                test_prompt = "Say 'Hello, openai is working!'"
                response = await self.generate_answer(test_prompt, max_tokens=50)
                if response:
                    results["openai_chat"] = True
                    logger.info("✅ OPENAI chat test passed")
            
            logger.info(f"📊 Connection test results: {results}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {str(e)}")
            return results


# Global enhanced LLM client instance
llm_client = LLMClient()
