#!/usr/bin/env python3
"""
Startup script for County Health Data API
Handles PORT environment variable properly for deployment platforms
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting County Health Data API on port {port}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )