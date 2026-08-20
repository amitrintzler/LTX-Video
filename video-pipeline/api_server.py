#!/usr/bin/env python3
"""
Launch the LTX Video Pipeline REST API server.

Run:
    python api_server.py

Then visit: http://localhost:8080
"""

import sys
from pathlib import Path

# Add parent directory to path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8080,
        workers=1,  # MUST be 1 — in-memory store is not multi-process safe
    )
