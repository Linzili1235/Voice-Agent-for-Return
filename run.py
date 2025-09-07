#!/usr/bin/env python3
# 应用启动脚本 - 用于开发和测试环境启动应用
import os
import sys
import uvicorn

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("Warning: .env file not found. Please copy .env.example to .env and configure it.")
        print("Using default settings for development...")
    
    # Start the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
