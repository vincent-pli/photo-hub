#!/usr/bin/env python3
"""Run photo-hub web server directly from source."""

import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the app
from photo_hub.web.api import app
import uvicorn

if __name__ == "__main__":
    print("Starting photo-hub web server from source...")
    print(f"API documentation: http://localhost:8000/docs")
    print(f"Default database: ~/.photo-hub/database.db")
    print("\nNote: To use AI features, set environment variables:")
    print("  For Gemini: export GOOGLE_API_KEY='your-key'")
    print("  For Qwen: export QWEN_API_KEY='your-key'")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )