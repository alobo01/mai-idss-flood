#!/usr/bin/env python3
"""
Run the FastAPI backend server
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    print(f"Starting Flood Prediction API on {host}:{port}")
    print(f"Database: {os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5439')}")
    print(f"Docs available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
