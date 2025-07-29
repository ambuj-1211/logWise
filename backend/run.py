#!/usr/bin/env python3
"""
Entry point for logWise backend.
Run this from the backend directory: python run.py
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting logWise Backend...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative docs: http://localhost:8000/redoc")
    print("🏥 Health check: http://localhost:8000/health")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 