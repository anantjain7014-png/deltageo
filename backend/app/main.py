import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.config import settings, FRONTEND_DIR
from backend.app.api.endpoints import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["Change Detection"])

# Serve Frontend static assets
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    landing_file = FRONTEND_DIR / "landing.html"
    if landing_file.exists():
        return FileResponse(str(landing_file))
    return {
        "status": "online",
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "api": settings.API_V1_STR
    }

@app.get("/dashboard")
@app.get("/index.html")
def serve_dashboard():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"error": "Dashboard not found"}

@app.get("/favicon.ico")
def serve_favicon():
    return FileResponse(str(FRONTEND_DIR / "favicon.ico")) if (FRONTEND_DIR / "favicon.ico").exists() else {}
