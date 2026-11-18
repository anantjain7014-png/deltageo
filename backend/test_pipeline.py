import os
import sys
from pathlib import Path
import numpy as np

# Ensure root directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings, SAMPLES_DIR
from backend.app.services.preprocessor import ImagePreprocessor
from backend.app.services.model_service import ModelService
from backend.app.services.postprocessor import PostProcessor
from backend.app.services.report_service import ReportService

def test_full_pipeline():
    print("==================================================")
    print("Testing Change Detection Pipeline...")
    print("==================================================")

    # 1. Preprocessor Test
    pre = ImagePreprocessor(target_size=(256, 256))
    t1_path = SAMPLES_DIR / "urban_expansion_t1.png"
    t2_path = SAMPLES_DIR / "urban_expansion_t2.png"

    assert t1_path.exists(), f"Sample T1 missing: {t1_path}"
    assert t2_path.exists(), f"Sample T2 missing: {t2_path}"

    with open(t1_path, "rb") as f1, open(t2_path, "rb") as f2:
        b1, b2 = f1.read(), f2.read()

    arr1 = pre.decode_image_bytes(b1)
    arr2 = pre.decode_image_bytes(b2)
    assert arr1.shape == (256, 256, 3)
    assert arr2.shape == (256, 256, 3)
    print("-> [PASS] Image decoding & validation")

    arr1, arr2_aligned = pre.align_radiometry(arr1, arr2)
    t1, t2, _ = pre.prepare_input_tensors(arr1, arr2_aligned)
    assert t1.shape == (1, 256, 256, 3)
    assert t2.shape == (1, 256, 256, 3)
    print("-> [PASS] Radiometric alignment & tensor scaling")

    # 2. Model Forward Pass Test
    model_srv = ModelService.get_instance()
    prob_map, inf_time = model_srv.predict_change(t1, t2)
    assert prob_map.shape == (256, 256)
    assert 0.0 <= np.min(prob_map) <= np.max(prob_map) <= 1.0
    print(f"-> [PASS] Siamese forward pass executed in {inf_time:.2f} ms")

    # 3. Post-Processing & Filtering Test
    post = PostProcessor(resolution_meters=5.0)
    metrics, clusters, mask_b64, overlay_b64, heatmap_b64, _, _ = post.process_detection(
        prob_map=prob_map,
        img_t1=arr1,
        img_t2=arr2,
        confidence_threshold=0.50,
        min_area_sq_meters=50.0,
        filter_natural_changes=True,
        sensor_type="Sentinel-2 MSI",
        processing_time_ms=inf_time
    )

    assert metrics.total_change_area_sq_meters > 0
    assert len(clusters) > 0
    assert mask_b64.startswith("data:image/png;base64,")
    assert overlay_b64.startswith("data:image/png;base64,")
    print(f"-> [PASS] Detected {len(clusters)} human activity clusters, Total Area: {metrics.total_change_area_sq_meters:,.1f} m²")
    print(f"-> [PASS] Dominant activity: {metrics.dominant_activity}")

    # 4. GeoJSON & PDF Report Test
    geojson = ReportService.generate_geojson(clusters, metrics)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == len(clusters)
    print(f"-> [PASS] GeoJSON export generated with {len(geojson['features'])} vector features")

    pdf_bytes = ReportService.generate_pdf_report(metrics, clusters, b1, b2, b"")
    assert len(pdf_bytes) > 1000
    print(f"-> [PASS] PDF report compiled successfully ({len(pdf_bytes):,} bytes)")

    print("==================================================")
    print("ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_full_pipeline()
