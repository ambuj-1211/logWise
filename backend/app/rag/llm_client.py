"""
LiteLLM client for Gemini embeddings and completions.
Reference: https://github.com/groq-ai/litellm
"""
import logging
import os
from typing import List

import litellm
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LitellmClient:
    """Client for LiteLLM operations with Gemini models."""
    
    def __init__(self, api_key: str = None):
        """Initialize LiteLLM client with API key."""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        logger.info("🔑 Initializing LiteLLM Client...")
        
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY environment variable is required!")
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Check if API key is valid format (not empty, has reasonable length)
        if len(self.api_key) < 10:
            logger.error("❌ API key seems too short. Please check your GEMINI_API_KEY")
            raise ValueError("Invalid API key format")
        
        logger.info(f"✅ API Key found: {self.api_key[:10]}...{self.api_key[-4:]}")
        
        # Configure LiteLLM
        litellm.api_key = self.api_key
        logger.info("🔧 LiteLLM configured with API key")
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Gemini embeddings.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"🧠 Generating embeddings for {len(texts)} text(s)")
        
        for i, text in enumerate(texts):
            logger.info(f"📝 Text {i+1}: {text[:100]}{'...' if len(text) > 100 else ''}")
        
        try:
            logger.info("🚀 Calling LiteLLM embedding API...")
            embeddings = await litellm.embedding(
                model="gemini/gemini-embedding-001",
                input=texts
            )
            
            # Extract embedding vectors
            embedding_vectors = [embedding["embedding"] for embedding in embeddings["data"]]
            
            logger.info(f"✅ Successfully generated {len(embedding_vectors)} embeddings")
            logger.info(f"📊 Embedding dimensions: {len(embedding_vectors[0]) if embedding_vectors else 0}")
            
            # Log some stats about the embeddings
            for i, embedding in enumerate(embedding_vectors):
                logger.info(f"📈 Embedding {i+1} stats - Length: {len(embedding)}, "
                          f"Min: {min(embedding):.4f}, Max: {max(embedding):.4f}, "
                          f"Mean: {sum(embedding)/len(embedding):.4f}")
            
            return embedding_vectors
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {str(e)}")
            logger.error(f"🔍 Error type: {type(e).__name__}")
            raise Exception(f"Embedding generation failed: {str(e)}")
    
    async def generate_answer(self, prompt: str) -> str:
        """
        Generate a completion using Gemini Ultra.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Generated text response
        """
        logger.info("🤖 Generating completion with Gemini Ultra...")
        logger.info(f"📝 Prompt length: {len(prompt)} characters")
        logger.info(f"📄 Prompt preview: {prompt[:200]}{'...' if len(prompt) > 200 else ''}")
        
        try:
            logger.info("🚀 Calling LiteLLM completion API...")
            response = await litellm.completion(
                model="gemini/gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            logger.info(f"✅ Successfully generated completion")
            logger.info(f"📝 Response length: {len(answer)} characters")
            logger.info(f"💬 Response preview: {answer[:200]}{'...' if len(answer) > 200 else ''}")
            
            # Log usage statistics if available
            if hasattr(response, 'usage'):
                usage = response.usage
                logger.info(f"📊 Usage - Tokens: {usage.total_tokens}, "
                          f"Prompt: {usage.prompt_tokens}, "
                          f"Completion: {usage.completion_tokens}")
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Completion generation failed: {str(e)}")
            logger.error(f"🔍 Error type: {type(e).__name__}")
            raise Exception(f"Completion generation failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test if the LLM client can connect and authenticate."""
        logger.info("🧪 Testing LLM client connection...")
        
        try:
            # Test with a simple embedding
            import asyncio
            
            async def test():
                test_texts = ["Hello, world!"]
                embeddings = await self.embed_texts(test_texts)
                return len(embeddings) > 0 and len(embeddings[0]) > 0
            
            result = asyncio.run(test())
            
            if result:
                logger.info("✅ LLM client connection test passed!")
                return True
            else:
                logger.error("❌ LLM client connection test failed!")
                return False
                
        except Exception as e:
            logger.error(f"❌ LLM client connection test failed: {str(e)}")
            return False


# Global client instance
llm_client = LitellmClient()
