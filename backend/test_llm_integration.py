#!/usr/bin/env python3
"""
Comprehensive LLM Integration Test for logWise Backend
This script tests the entire RAG pipeline including embeddings and completions.
"""
import asyncio
import logging
import os
import sys
from typing import Any, Dict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_llm_client():
    """Test the LLM client initialization and basic functionality."""
    print("\n" + "="*60)
    print("🧪 Testing LLM Client")
    print("="*60)
    
    try:
        from app.rag.llm_client import llm_client

        # Test API key
        print("🔑 Testing API key...")
        if not llm_client.api_key:
            print("❌ No API key found!")
            return False
        
        print(f"✅ API key found: {llm_client.api_key[:10]}...{llm_client.api_key[-4:]}")
        
        # Test connection
        print("🧪 Testing LLM connection...")
        if llm_client.test_connection():
            print("✅ LLM connection test passed!")
        else:
            print("❌ LLM connection test failed!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ LLM client test failed: {str(e)}")
        return False

async def test_embeddings():
    """Test embedding generation."""
    print("\n" + "="*60)
    print("🧠 Testing Embeddings")
    print("="*60)
    
    try:
        from app.rag.llm_client import llm_client

        # Test texts
        test_texts = [
            "Hello, this is a test log entry",
            "Error: Connection timeout occurred",
            "Container started successfully",
            "Warning: High memory usage detected"
        ]
        
        print(f"📝 Testing embeddings for {len(test_texts)} texts...")
        
        for i, text in enumerate(test_texts):
            print(f"   📄 Text {i+1}: {text}")
        
        # Generate embeddings
        embeddings = await llm_client.embed_texts(test_texts)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        
        # Check embedding properties
        for i, embedding in enumerate(embeddings):
            print(f"📊 Embedding {i+1}:")
            print(f"   📏 Dimensions: {len(embedding)}")
            print(f"   📈 Min: {min(embedding):.4f}")
            print(f"   📈 Max: {max(embedding):.4f}")
            print(f"   📈 Mean: {sum(embedding)/len(embedding):.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding test failed: {str(e)}")
        return False

async def test_completions():
    """Test completion generation."""
    print("\n" + "="*60)
    print("🤖 Testing Completions")
    print("="*60)
    
    try:
        from app.rag.llm_client import llm_client

        # Test prompts
        test_prompts = [
            "What is Docker?",
            "Explain containerization in simple terms",
            "What are the benefits of using containers?"
        ]
        
        print(f"📝 Testing completions for {len(test_prompts)} prompts...")
        
        for i, prompt in enumerate(test_prompts):
            print(f"\n📄 Prompt {i+1}: {prompt}")
            
            # Generate completion
            response = await llm_client.generate_answer(prompt)
            
            print(f"💬 Response {i+1}: {response[:200]}{'...' if len(response) > 200 else ''}")
            print(f"📏 Response length: {len(response)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Completion test failed: {str(e)}")
        return False

async def test_vector_store():
    """Test vector store operations."""
    print("\n" + "="*60)
    print("🗄️  Testing Vector Store")
    print("="*60)
    
    try:
        import uuid
        from datetime import datetime

        from app.rag.llm_client import llm_client
        from app.storage.vector_store import LogChunk, vector_store

        # Test data
        test_chunks = [
            LogChunk(
                text="Container started successfully at 2024-01-01 10:00:00",
                container_id="test_container_1",
                timestamp=datetime.now().isoformat(),
                chunk_id=f"test_{uuid.uuid4().hex[:8]}",
                metadata={"test": True}
            ),
            LogChunk(
                text="Error: Connection timeout occurred at 2024-01-01 10:05:00",
                container_id="test_container_1",
                timestamp=datetime.now().isoformat(),
                chunk_id=f"test_{uuid.uuid4().hex[:8]}",
                metadata={"test": True}
            ),
            LogChunk(
                text="Warning: High memory usage detected at 2024-01-01 10:10:00",
                container_id="test_container_1",
                timestamp=datetime.now().isoformat(),
                chunk_id=f"test_{uuid.uuid4().hex[:8]}",
                metadata={"test": True}
            )
        ]
        
        print(f"📝 Testing vector store with {len(test_chunks)} chunks...")
        
        # Generate embeddings for test chunks
        texts = [chunk.text for chunk in test_chunks]
        embeddings = await llm_client.embed_texts(texts)
        
        # Upsert chunks
        await vector_store.upsert_chunks(test_chunks, embeddings)
        print("✅ Successfully upserted test chunks")
        
        # Test query
        query_text = "What errors occurred?"
        print(f"🔍 Testing query: {query_text}")
        
        # Generate query embedding
        query_embeddings = await llm_client.embed_texts([query_text])
        query_embedding = query_embeddings[0]
        
        # Query vector store
        results = await vector_store.query_similar(
            query_embedding=query_embedding,
            container_id="test_container_1",
            k=3
        )
        
        print(f"📚 Query returned {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"📄 Result {i+1}:")
            print(f"   📝 Text: {result['text']}")
            print(f"   🏷️  Metadata: {result['metadata']}")
            if result.get('distance'):
                print(f"   📏 Distance: {result['distance']:.4f}")
        
        # Get stats
        stats = vector_store.get_stats()
        print(f"📊 Vector store stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector store test failed: {str(e)}")
        return False

async def test_rag_pipeline():
    """Test the complete RAG pipeline."""
    print("\n" + "="*60)
    print("🔗 Testing Complete RAG Pipeline")
    print("="*60)
    
    try:
        from app.rag.retriever import rag_retriever

        # Test query
        container_id = "test_container_1"
        question = "What errors occurred in the logs?"
        
        print(f"🔍 Testing RAG pipeline:")
        print(f"   🐳 Container ID: {container_id}")
        print(f"   ❓ Question: {question}")
        
        # Retrieve context
        docs = await rag_retriever.retrieve_context(
            container_id=container_id,
            question=question,
            k=3
        )
        
        print(f"📚 Retrieved {len(docs)} documents")
        
        if docs:
            # Build prompt
            prompt = rag_retriever.build_prompt(docs, question)
            print(f"📝 Built prompt ({len(prompt)} characters)")
            
            # Generate answer
            from app.rag.llm_client import llm_client
            answer = await llm_client.generate_answer(prompt)
            
            print(f"💬 Generated answer ({len(answer)} characters):")
            print(f"   {answer}")
            
            # Extract references
            references = rag_retriever.extract_references(docs)
            print(f"📋 Extracted {len(references)} references")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG pipeline test failed: {str(e)}")
        return False

async def test_api_endpoints():
    """Test API endpoints."""
    print("\n" + "="*60)
    print("🌐 Testing API Endpoints")
    print("="*60)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        print("🏥 Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"📊 Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test query suggestions
        print("💡 Testing query suggestions...")
        response = requests.get(f"{base_url}/api/logs/query/suggestions")
        if response.status_code == 200:
            suggestions = response.json()
            print(f"✅ Query suggestions working - {len(suggestions)} suggestions")
        else:
            print(f"❌ Query suggestions failed: {response.status_code}")
            return False
        
        # Test query endpoint
        print("🤖 Testing query endpoint...")
        query_data = {
            "container_id": "test_container_1",
            "question": "What errors occurred?",
            "k": 3
        }
        response = requests.post(f"{base_url}/api/logs/query", json=query_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Query endpoint working")
            print(f"📝 Answer: {result['answer'][:200]}{'...' if len(result['answer']) > 200 else ''}")
        else:
            print(f"❌ Query endpoint failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoints test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Comprehensive LLM Integration Test")
    print("="*80)
    
    tests = [
        ("LLM Client", test_llm_client),
        ("Embeddings", test_embeddings),
        ("Completions", test_completions),
        ("Vector Store", test_vector_store),
        ("RAG Pipeline", test_rag_pipeline),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 Test Results Summary")
    print("="*80)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Your LLM integration is working perfectly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check your GEMINI_API_KEY environment variable")
        print("2. Ensure the backend is running on port 8000")
        print("3. Check your internet connection for API calls")
        print("4. Verify Docker is running for container tests")

if __name__ == "__main__":
    asyncio.run(main()) 