#!/usr/bin/env python3
"""
Simple synchronous test script to check if LiteLLM can use Gemini API key
for embeddings and completions (no async/await, correct model/function names).
"""
import os

import litellm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_api_key():
    """Test if API key is loaded correctly."""
    print("🔑 Testing API Key...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables!")
        print("💡 Make sure you have a .env file with GEMINI_API_KEY=your_key_here")
        return False
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    print(f"📏 API key length: {len(api_key)} characters")
    if len(api_key) < 10:
        print("⚠️  Warning: API key seems too short")
        return False
    return True

def test_embedding():
    """Test LiteLLM embedding with Gemini (sync)."""
    print("\n🧠 Testing LiteLLM Embedding...")
    try:
        litellm.api_key = os.getenv("GEMINI_API_KEY")
        test_text = "Hello, this is a test for embedding generation"
        print(f"📝 Test text: {test_text}")
        print("🚀 Calling LiteLLM embedding API...")
        embeddings = litellm.embedding(
            model="gemini/text-embedding-004",
            input=[test_text]
        )
        embedding_vector = embeddings["data"][0]["embedding"]
        print(f"✅ Embedding generated successfully!")
        print(f"The generated embeddings variable is {embeddings}")
        print(f"📊 Embedding dimensions: {len(embedding_vector)}")
        print(f"📈 Min value: {min(embedding_vector):.4f}")
        print(f"📈 Max value: {max(embedding_vector):.4f}")
        print(f"📈 Mean value: {sum(embedding_vector)/len(embedding_vector):.4f}")
        return True
    except Exception as e:
        print(f"❌ Embedding test failed: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

def test_completion():
    """Test LiteLLM completion with Gemini (sync)."""
    print("\n🤖 Testing LiteLLM Completion...")
    try:
        litellm.api_key = os.getenv("GEMINI_API_KEY")
        test_prompt = "What is Docker? Explain in one sentence."
        print(f"📝 Test prompt: {test_prompt}")
        print("🚀 Calling LiteLLM completion API...")
        response = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=[{"role": "user", "content": test_prompt}],
            temperature=0.1,
            max_tokens=100
        )
        answer = response.choices[0].message.content
        print(f"✅ Completion generated successfully!")
        print(f"The generated response is {response} and its type is {type(response)}")
        print(f"💬 Response: {answer}")
        print(f"📏 Response length: {len(answer)} characters")
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"📊 Usage - Total tokens: {usage.total_tokens}")
        return True
    except Exception as e:
        print(f"❌ Completion test failed: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

def main():
    print("🧪 Simple LiteLLM Test (Synchronous)")
    print("="*50)
    if not test_api_key():
        print("\n❌ API key test failed. Cannot proceed.")
        return
    embedding_success = test_embedding()
    completion_success = test_completion()
    print("\n" + "="*50)
    print("📊 Test Results")
    print("="*50)
    print(f"🔑 API Key: ✅ PASS")
    print(f"🧠 Embedding: {'✅ PASS' if embedding_success else '❌ FAIL'}")
    print(f"🤖 Completion: {'✅ PASS' if completion_success else '❌ FAIL'}")
    if embedding_success and completion_success:
        print("\n🎉 All tests passed! LiteLLM is working correctly with your Gemini API key.")
        print("✅ You can use embeddings and completions in your project.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        print("🔧 Troubleshooting tips:")
        print("1. Verify your GEMINI_API_KEY is correct")
        print("2. Check your internet connection")
        print("3. Ensure you have sufficient API quota")
        print("4. Try regenerating your API key if needed")

if __name__ == "__main__":
    main() 