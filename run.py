#!/usr/bin/env python3
"""Run the Pixel Knight server."""
import uvicorn
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.config import settings

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                     PIXEL KNIGHT                         ║
    ║              AI Chat Interface with RAG                  ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Server: http://localhost:{port:<6}                        ║
    ║  API:    {api:<43} ║
    ╚══════════════════════════════════════════════════════════╝
    """.format(port=settings.port, api=settings.openai_api_base))
    
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
