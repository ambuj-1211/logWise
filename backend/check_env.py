#!/usr/bin/env python3
"""
Check environment variables and API key setup for logWise Backend
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def check_env():
    """Check environment variables."""
    print("🔍 Checking Environment Variables")
    print("="*50)
    
    # Check GEMINI_API_KEY
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"✅ GEMINI_API_KEY found: {api_key[:10]}...{api_key[-4:]}")
        print(f"📏 API key length: {len(api_key)} characters")
        
        if len(api_key) < 10:
            print("⚠️  Warning: API key seems too short")
        else:
            print("✅ API key length looks good")
    else:
        print("❌ GEMINI_API_KEY not found!")
        print("💡 Set it with: export GEMINI_API_KEY='your_api_key_here'")
        return False
    
    # Check other environment variables
    env_vars = [
        "CHROMA_PERSIST_DIR",
        "PYTHONPATH",
        "DOCKER_HOST"
    ]
    
    print("\n📋 Other Environment Variables:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"ℹ️  {var}: Not set (optional)")
    
    return True

def check_docker():
    """Check Docker availability."""
    print("\n🐳 Checking Docker...")
    
    try:
        import docker
        client = docker.from_env()
        
        # Test Docker connection
        client.ping()
        print("✅ Docker daemon is running")
        
        # List containers
        containers = client.containers.list()
        print(f"📦 Found {len(containers)} running containers")
        
        for container in containers:
            print(f"   - {container.name} ({container.id[:12]}) - {container.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Docker check failed: {str(e)}")
        return False

def check_python_deps():
    """Check Python dependencies."""
    print("\n🐍 Checking Python Dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "docker",
        "chromadb",
        "litellm",
        "pydantic"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing!")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def main():
    """Run all checks."""
    print("🧪 Environment Check for logWise Backend")
    print("="*60)
    
    checks = [
        ("Environment Variables", check_env),
        ("Docker", check_docker),
        ("Python Dependencies", check_python_deps),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Check {check_name} failed: {str(e)}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Check Results Summary")
    print("="*60)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("🎉 All checks passed! Your environment is ready.")
        print("\n🚀 Next steps:")
        print("1. Start the backend: python run.py")
        print("2. Test the API: python test_llm_integration.py")
        print("3. Start the frontend: cd ../ui && npm run dev")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")

if __name__ == "__main__":
    main() 