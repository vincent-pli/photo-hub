"""Main entry point for photo-hub web server."""

import sys
import uvicorn
from .api import app

def main():
    """Run the web server."""
    print("Starting photo-hub web server...")
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
        reload=False  # Set to True for development
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)