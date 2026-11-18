from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DetectedCluster(BaseModel):
    id: int
    category: str
    confidence: float
    area_sq_meters: float
    area_hectares: float
    bbox: List[int] = Field(..., description="[min_x, min_y, max_x, max_y]")
    centroid: List[float] = Field(..., description="[centroid_x, centroid_y]")
    severity: str = Field(..., description="HIGH | MEDIUM | LOW")

class DetectionMetrics(BaseModel):
    total_image_area_sq_meters: float
    total_change_area_sq_meters: float
    total_change_area_hectares: float
    natural_filtered_area_sq_meters: float
    change_percentage: float
    total_clusters: int
    dominant_activity: str
    class_distribution: Dict[str, float]
    sensor_type: str
    resolution_meters: float
    processing_time_ms: float

class DetectionResponse(BaseModel):
    success: bool
    message: str
    metrics: DetectionMetrics
    clusters: List[DetectedCluster]
    mask_base64: str
    overlay_base64: str
    heatmap_base64: str
    t1_base64: str
    t2_base64: str

class SamplePair(BaseModel):
    id: str
    title: str
    sensor: str
    location: str
    description: str
    expected_activity: str
    t1_thumb: str
    t2_thumb: str
    t1_path: str
    t2_path: str

class ModelInfoResponse(BaseModel):
    name: str
    architecture: str
    input_shape: List[int]
    supported_sensors: List[str]
    filter_capabilities: List[str]
    loaded: bool
    weights_path: str
