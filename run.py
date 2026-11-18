import uvicorn
import os
import sys

if __name__ == "__main__":
    print("==================================================================")
    print("  Automated Human Activity Change Detection System")
    print("  FastAPI Backend & Satellite Telemetry Dashboard")
    print("==================================================================")
    print("-> Server running at: http://localhost:8080")
    print("-> API Documentation: http://localhost:8080/docs")
    print("==================================================================")
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False
    )
