import io
import base64
import json
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import JSONResponse

from backend.app.core.config import settings, SAMPLES_DIR
from backend.app.schemas.detection import DetectionResponse, SamplePair, ModelInfoResponse, DetectedCluster, DetectionMetrics
from backend.app.services.preprocessor import ImagePreprocessor
from backend.app.services.model_service import ModelService
from backend.app.services.postprocessor import PostProcessor
from backend.app.services.report_service import ReportService
from PIL import Image
import numpy as np

router = APIRouter()

preprocessor = ImagePreprocessor(target_size=settings.IMAGE_SIZE)
model_service = ModelService.get_instance()

@router.get("/health")
def get_health():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model_loaded": model_service.is_loaded
    }

@router.get("/model-info", response_model=ModelInfoResponse)
def get_model_info():
    info = model_service.get_info()
    return ModelInfoResponse(**info)

@router.get("/samples", response_model=List[SamplePair])
def get_samples():
    """Returns curated Sentinel-2 and LISS-4 sample bi-temporal pairs."""
    samples_list = [
        {
            "id": "urban_expansion",
            "title": "Urban Development & Construction",
            "sensor": "Sentinel-2 MSI (10m)",
            "location": "Suburban Periphery (28.4595° N, 77.0266° E)",
            "description": "Conversion of open rural ground into commercial buildings, residential blocks, and asphalt access roads.",
            "expected_activity": "Building & Urban Construction",
            "t1_file": "presentation_sample_t1.jpg",
            "t2_file": "presentation_sample_t2.jpg"
        },
        {
            "id": "road_construction",
            "title": "Highway Infrastructure Corridor",
            "sensor": "LISS-4 (5.8m Multispectral)",
            "location": "Expressway Expansion Zone (19.0760° N, 72.8777° E)",
            "description": "Rapid development of multi-lane highway, overpass ramp, and heavy transport logistics activity.",
            "expected_activity": "Road & Pavement Infrastructure",
            "t1_file": "road_before.jpg",
            "t2_file": "road_after.jpg"
        },
        {
            "id": "industrial_facility",
            "title": "Industrial Logistics Park",
            "sensor": "Cartosat Optical High-Res (2.5m)",
            "location": "Special Economic Zone (12.9716° N, 77.5946° E)",
            "description": "Erection of industrial manufacturing halls, storage silos, and logistics apron.",
            "expected_activity": "Industrial & Facility Expansion",
            "t1_file": "industrial_before.jpg",
            "t2_file": "industrial_after.jpg"
        }
    ]

    result = []
    for s in samples_list:
        p1 = SAMPLES_DIR / s["t1_file"]
        p2 = SAMPLES_DIR / s["t2_file"]
        
        t1_b64, t2_b64 = "", ""
        if p1.exists():
            with open(p1, "rb") as f:
                t1_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
        if p2.exists():
            with open(p2, "rb") as f:
                t2_b64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

        result.append(SamplePair(
            id=s["id"],
            title=s["title"],
            sensor=s["sensor"],
            location=s["location"],
            description=s["description"],
            expected_activity=s["expected_activity"],
            t1_thumb=t1_b64,
            t2_thumb=t2_b64,
            t1_path=str(p1),
            t2_path=str(p2)
        ))

    return result

@router.post("/detect", response_model=DetectionResponse)
async def detect_changes(
    image_t1: UploadFile = File(..., description="Pre-change satellite image (T1)"),
    image_t2: UploadFile = File(..., description="Post-change satellite image (T2)"),
    confidence_threshold: float = Form(0.50),
    min_area_sq_meters: float = Form(50.0),
    filter_natural_changes: bool = Form(True),
    sensor_type: str = Form("Sentinel-2 MSI"),
    resolution_meters: float = Form(5.0)
):
    """
    Main Bi-Temporal Change Detection Pipeline.
    1. Loads T1 & T2 images
    2. Runs Siamese inference
    3. Post-processes & filters results variations.
    """
    try:
        # Read bytes
        bytes_t1 = await image_t1.read()
        bytes_t2 = await image_t2.read()

        # Decode
        arr_t1 = preprocessor.decode_image_bytes(bytes_t1)
        arr_t2 = preprocessor.decode_image_bytes(bytes_t2)

        # Radiometric alignment
        arr_t1, arr_t2_aligned = preprocessor.align_radiometry(arr_t1, arr_t2)

        # Prepare normalized tensors [1, 256, 256, 3]
        tensor_t1, tensor_t2, orig_dim = preprocessor.prepare_input_tensors(arr_t1, arr_t2_aligned)

        # AI Siamese Forward Pass
        prob_map, inference_ms = model_service.predict_change(tensor_t1, tensor_t2)

        # Resize prob_map back to original dimensions
        prob_map = np.array(Image.fromarray(prob_map).resize((orig_dim[1], orig_dim[0]), Image.Resampling.BILINEAR))

        # Post-processing & Anthropogenic Classification
        post = PostProcessor(resolution_meters=resolution_meters)
        metrics, clusters, mask_b64, overlay_b64, heatmap_b64, t1_b64, t2_b64 = post.process_detection(
            prob_map=prob_map,
            img_t1=arr_t1,
            img_t2=arr_t2,
            confidence_threshold=confidence_threshold,
            min_area_sq_meters=min_area_sq_meters,
            filter_natural_changes=filter_natural_changes,
            sensor_type=sensor_type,
            processing_time_ms=inference_ms
        )

        return DetectionResponse(
            success=True,
            message="Human activity change detection completed successfully.",
            metrics=metrics,
            clusters=clusters,
            mask_base64=mask_b64,
            overlay_base64=overlay_b64,
            heatmap_base64=heatmap_b64,
            t1_base64=t1_b64,
            t2_base64=t2_b64
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference pipeline failed: {str(e)}")

@router.post("/detect-sample/{sample_id}", response_model=DetectionResponse)
def detect_sample(
    sample_id: str,
    confidence_threshold: float = 0.50,
    min_area_sq_meters: float = 50.0,
    filter_natural_changes: bool = True
):
    """Executes detection on a selected sample pair from the pre-loaded dataset."""
    t1_file = SAMPLES_DIR / f"{sample_id}_t1.png"
    t2_file = SAMPLES_DIR / f"{sample_id}_t2.png"

    if not t1_file.exists() or not t2_file.exists():
        raise HTTPException(status_code=404, detail=f"Sample pair '{sample_id}' not found.")

    with open(t1_file, "rb") as f1, open(t2_file, "rb") as f2:
        bytes_t1 = f1.read()
        bytes_t2 = f2.read()

    arr_t1 = preprocessor.decode_image_bytes(bytes_t1)
    arr_t2 = preprocessor.decode_image_bytes(bytes_t2)

    arr_t1, arr_t2_aligned = preprocessor.align_radiometry(arr_t1, arr_t2)
    tensor_t1, tensor_t2, orig_dim = preprocessor.prepare_input_tensors(arr_t1, arr_t2_aligned)

    prob_map, inference_ms = model_service.predict_change(tensor_t1, tensor_t2)
    
    # Resize prob_map back to original dimensions
    prob_map = np.array(Image.fromarray(prob_map).resize((orig_dim[1], orig_dim[0]), Image.Resampling.BILINEAR))

    post = PostProcessor(resolution_meters=settings.DEFAULT_RESOLUTION_METERS)
    metrics, clusters, mask_b64, overlay_b64, heatmap_b64, t1_b64, t2_b64 = post.process_detection(
        prob_map=prob_map,
        img_t1=arr_t1,
        img_t2=arr_t2,
        confidence_threshold=confidence_threshold,
        min_area_sq_meters=min_area_sq_meters,
        filter_natural_changes=filter_natural_changes,
        sensor_type="Sentinel-2 MSI",
        processing_time_ms=inference_ms
    )

    return DetectionResponse(
        success=True,
        message=f"Sample '{sample_id}' analyzed successfully.",
        metrics=metrics,
        clusters=clusters,
        mask_base64=mask_b64,
        overlay_base64=overlay_b64,
        heatmap_base64=heatmap_b64,
        t1_base64=t1_b64,
        t2_base64=t2_b64
    )

@router.post("/export/geojson")
def export_geojson(payload: dict):
    """Exports detection result clusters to standard GeoJSON."""
    try:
        clusters = [DetectedCluster(**c) for c in payload.get("clusters", [])]
        metrics = DetectionMetrics(**payload.get("metrics", {}))
        geojson_data = ReportService.generate_geojson(clusters, metrics)
        return JSONResponse(content=geojson_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GeoJSON export failed: {str(e)}")

@router.post("/export/report")
def export_report(payload: dict):
    """Generates downloadable PDF audit report."""
    try:
        clusters = [DetectedCluster(**c) for c in payload.get("clusters", [])]
        metrics = DetectionMetrics(**payload.get("metrics", {}))
        
        pdf_bytes = ReportService.generate_pdf_report(
            metrics=metrics,
            clusters=clusters,
            t1_bytes=b"",
            t2_bytes=b"",
            overlay_bytes=b""
        )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Change_Detection_Report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF generation failed: {str(e)}")
