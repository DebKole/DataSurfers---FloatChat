#!/usr/bin/env python3
"""
Startup script for FloatChat application.
This script starts the FastAPI server with proper configuration.
"""

import uvicorn
import os
from pathlib import Path

def main():
    """Start the FloatChat server."""
    
    print("🚀 Starting FloatChat Server...")
    print("📊 Loading Argo float data...")
    
    # Check if data file exists
    data_file = Path("argo_demo.csv")
    if not data_file.exists():
        print("❌ Error: argo_demo.csv not found!")
        print("Please make sure the data file is in the current directory.")
        return
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("Some features may not work without GEMINI_API_KEY")
    
    print("✅ Data file found")
    print("🌐 Starting server on http://127.0.0.1:8000")
    print("📱 Make sure your React frontend is running on http://localhost:3000")
    print("\n" + "="*50)
    print("FloatChat is ready! 🤖")
    print("="*50 + "\n")
    
    # Start the server
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()