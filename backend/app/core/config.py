import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
SAMPLES_DIR = BACKEND_DIR / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = BASE_DIR / "best_siamese_unet_model.keras"

class Settings(BaseModel):
    PROJECT_NAME: str = "DeltaGeo"
    PROJECT_DESCRIPTION: str = "AI-powered automated bi-temporal remote sensing change detection for anthropogenic activities (Sentinel-2 & LISS-4)"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Model configuration
    MODEL_FILE: Path = MODEL_PATH
    IMAGE_SIZE: tuple[int, int] = (256, 256)
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.30
    DEFAULT_MIN_AREA_SQ_METERS: float = 20.0  # Min human structure area threshold
    
    # Ground Resolution in meters per pixel (Sentinel-2 ~ 10m/px, LISS-4 ~ 5.8m/px, High-Res ~ 1-2m/px)
    DEFAULT_RESOLUTION_METERS: float = 5.0
    
    # Supported human activity categories
    ACTIVITY_CLASSES: list[str] = [
        "Building & Urban Construction",
        "Road & Pavement Infrastructure",
        "Excavation & Cleared Ground",
        "Industrial & Facility Expansion",
        "Vehicle & Logistics Movement"
    ]

settings = Settings()
