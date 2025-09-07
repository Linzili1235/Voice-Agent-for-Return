#!/usr/bin/env python3
# 服务器启动脚本 - 用于启动 FastAPI HTTP Tools 服务器
import os
import sys
import uvicorn

# Add the server directory to Python path
server_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server')
sys.path.insert(0, server_dir)

if __name__ == "__main__":
    # Check if .env file exists
    env_file = os.path.join(server_dir, ".env")
    if not os.path.exists(env_file):
        print("Warning: .env file not found. Please copy .env.example to .env and configure it.")
        print("Using default settings for development...")
    
    # Start the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8787,
        reload=True,
        log_level="info"
    )

