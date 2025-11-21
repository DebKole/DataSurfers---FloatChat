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
        print("⚠️  Warning: argo_demo.csv not found!")
        print("Some legacy demo features depending on this file may not work.")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("Some features may not work without GEMINI_API_KEY")
    
    if data_file.exists():
        print("✅ Data file found")
    print("🌐 Starting server on http://0.0.0.0:8000 (accessible on your LAN)")
    print("📱 Make sure your React frontend is running on http://localhost:3000")
    print("\n" + "="*50)
    print("FloatChat is ready! 🤖")
    print("="*50 + "\n")
    
    # Start the server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()