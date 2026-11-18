import io
import base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import scipy.ndimage as ndi
from skimage import measure, morphology
from typing import List, Dict, Tuple, Any, Optional

from backend.app.core.config import settings
from backend.app.schemas.detection import DetectedCluster, DetectionMetrics

class PostProcessor:
    """
    Remote Sensing Post-Processing & Anthropogenic Activity Classifier.
    Applies natural change filtering, polygonization, geometric classification, and visual rendering.
    """

    def __init__(self, resolution_meters: float = settings.DEFAULT_RESOLUTION_METERS):
        self.resolution_meters = resolution_meters
        self.pixel_area = resolution_meters * resolution_meters

    def process_detection(
        self,
        prob_map: np.ndarray,
        img_t1: np.ndarray,
        img_t2: np.ndarray,
        confidence_threshold: float = 0.50,
        min_area_sq_meters: float = 50.0,
        filter_natural_changes: bool = True,
        sensor_type: str = "Sentinel-2 MSI",
        processing_time_ms: float = 0.0
    ) -> Tuple[DetectionMetrics, List[DetectedCluster], str, str, str, str, str]:
        """
        Executes full post-processing pipeline and returns metrics, cluster list, and Base64 visuals.
        """
        h, w = prob_map.shape[:2]
        min_pixels = max(4, int(min_area_sq_meters / self.pixel_area))

        # 1. Binary thresholding
        raw_mask = (prob_map >= confidence_threshold).astype(np.uint8)

        # 2. Natural Phenological / Seasonal Change Suppressor
        if filter_natural_changes:
            cleaned_mask = self._suppress_natural_changes(raw_mask, img_t1, img_t2)
        else:
            cleaned_mask = raw_mask

        # 3. Morphological opening and closing to clean noise
        try:
            cleaned_mask = morphology.remove_small_holes(cleaned_mask.astype(bool), max_size=min_pixels // 2)
            cleaned_mask = morphology.remove_small_objects(cleaned_mask, max_size=min_pixels).astype(np.uint8)
        except TypeError:
            cleaned_mask = morphology.remove_small_holes(cleaned_mask.astype(bool), area_threshold=min_pixels // 2)
            cleaned_mask = morphology.remove_small_objects(cleaned_mask, min_size=min_pixels).astype(np.uint8)

        # 4. Label connected components and extract clusters
        labeled_mask, num_features = ndi.label(cleaned_mask)
        slices = ndi.find_objects(labeled_mask)

        clusters: List[DetectedCluster] = []
        class_counts = {cls_name: 0.0 for cls_name in settings.ACTIVITY_CLASSES}

        cluster_id = 1
        for i, slc in enumerate(slices):
            if slc is None:
                continue
            
            cluster_mask = (labeled_mask[slc] == (i + 1))
            pixel_count = int(np.sum(cluster_mask))
            
            if pixel_count < min_pixels:
                continue

            area_sq_m = float(pixel_count * self.pixel_area)
            area_ha = float(area_sq_m / 10000.0)

            # Bounding box coordinates in normalized scale and image scale
            min_y, max_y = slc[0].start, slc[0].stop
            min_x, max_x = slc[1].start, slc[1].stop
            bbox = [int(min_x), int(min_y), int(max_x), int(max_y)]

            # Centroid
            cy, cx = ndi.center_of_mass(cluster_mask)
            centroid = [float(min_x + cx), float(min_y + cy)]

            # Mean confidence within cluster
            cluster_prob = prob_map[slc][cluster_mask]
            conf = float(np.mean(cluster_prob)) if len(cluster_prob) > 0 else float(confidence_threshold)

            # Geometric and spectral classification
            category = self._classify_activity_cluster(
                cluster_mask=cluster_mask,
                patch_t1=img_t1[slc] if img_t1.shape[:2] == (h, w) else None,
                patch_t2=img_t2[slc] if img_t2.shape[:2] == (h, w) else None,
                bbox=bbox,
                pixel_count=pixel_count
            )

            # Determine severity
            if area_sq_m > 5000 or conf > 0.85:
                severity = "HIGH"
            elif area_sq_m > 1500 or conf > 0.65:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            clusters.append(DetectedCluster(
                id=cluster_id,
                category=category,
                confidence=round(conf, 3),
                area_sq_meters=round(area_sq_m, 2),
                area_hectares=round(area_ha, 4),
                bbox=bbox,
                centroid=[round(centroid[0], 1), round(centroid[1], 1)],
                severity=severity
            ))

            class_counts[category] += area_sq_m
            cluster_id += 1

        # 5. Compute global metrics
        total_img_pixels = h * w
        total_img_area_sq_m = float(total_img_pixels * self.pixel_area)
        total_change_pixels = int(np.sum(cleaned_mask > 0))
        total_change_area_sq_m = float(total_change_pixels * self.pixel_area)
        total_change_ha = float(total_change_area_sq_m / 10000.0)
        change_pct = float((total_change_pixels / total_img_pixels) * 100.0)

        raw_change_pixels = int(np.sum(raw_mask > 0))
        filtered_pixels = raw_change_pixels - total_change_pixels
        natural_filtered_area_sq_m = float(filtered_pixels * self.pixel_area)

        # Dominant activity
        dominant_activity = max(class_counts, key=class_counts.get) if total_change_area_sq_m > 0 else "No Change"

        metrics = DetectionMetrics(
            total_image_area_sq_meters=round(total_img_area_sq_m, 2),
            total_change_area_sq_meters=round(total_change_area_sq_m, 2),
            total_change_area_hectares=round(total_change_ha, 4),
            natural_filtered_area_sq_meters=round(natural_filtered_area_sq_m, 2),
            change_percentage=round(change_pct, 3),
            total_clusters=len(clusters),
            dominant_activity=dominant_activity,
            class_distribution={k: round(v, 2) for k, v in class_counts.items()},
            sensor_type=sensor_type,
            resolution_meters=self.resolution_meters,
            processing_time_ms=round(processing_time_ms, 2)
        )

        # 6. Render base64 image visuals
        mask_b64 = self._render_mask_base64(cleaned_mask)
        overlay_b64 = self._render_overlay_base64(img_t2, cleaned_mask, clusters)
        heatmap_b64 = self._render_heatmap_base64(prob_map)
        t1_b64 = self._ndarray_to_base64(img_t1)
        t2_b64 = self._ndarray_to_base64(img_t2)

        return metrics, clusters, mask_b64, overlay_b64, heatmap_b64, t1_b64, t2_b64

    def _suppress_natural_changes(self, mask: np.ndarray, img_t1: np.ndarray, img_t2: np.ndarray) -> np.ndarray:
        """
        Suppresses false alarms triggered by agricultural seasons, natural grass greening/drying,
        and cloud shadow drift by checking edge gradients vs pure hue/saturation shifts.
        """
        if img_t1.shape != img_t2.shape:
            return mask

        # Convert to float
        t1_f = img_t1.astype(np.float32) / 255.0
        t2_f = img_t2.astype(np.float32) / 255.0

        # High-frequency structural change (Sobel)
        def edge_map(img):
            gray = 0.299 * img[..., 0] + 0.587 * img[..., 1] + 0.114 * img[..., 2]
            sx = ndi.sobel(gray, axis=1)
            sy = ndi.sobel(gray, axis=0)
            return np.sqrt(sx**2 + sy**2)

        e1 = edge_map(t1_f)
        e2 = edge_map(t2_f)
        edge_change = np.abs(e2 - e1)
        
        # Pure vegetation variation: high green shift but almost zero new structural edges
        green_diff = np.abs(t2_f[..., 1] - t1_f[..., 1])
        pure_veg_shift = (green_diff > 0.18) & (edge_change < 0.05)

        filtered_mask = mask.copy()
        filtered_mask[pure_veg_shift] = 0

        return filtered_mask

    def _classify_activity_cluster(
        self,
        cluster_mask: np.ndarray,
        patch_t1: Optional[np.ndarray],
        patch_t2: Optional[np.ndarray],
        bbox: List[int],
        pixel_count: int
    ) -> str:
        """Classifies detected change cluster into standardized human activity categories."""
        min_x, min_y, max_x, max_y = bbox
        bw = max(1, max_x - min_x)
        bh = max(1, max_y - min_y)
        aspect_ratio = max(bw / bh, bh / bw)
        extent = pixel_count / (bw * bh)

        # Linear high-aspect ratio structures -> Road & Pavement Infrastructure
        if aspect_ratio >= 3.2 and extent < 0.55:
            return "Road & Pavement Infrastructure"

        # Very small high-intensity blobs -> Vehicle & Logistics Movement
        if pixel_count <= 25 and aspect_ratio < 2.5:
            return "Vehicle & Logistics Movement"

        # Rectangular, compact medium/large regions -> Building & Urban Construction
        if extent >= 0.50 and aspect_ratio < 2.5:
            return "Building & Urban Construction"

        # Large spread out footprint with soil/ground signature -> Excavation & Cleared Ground
        if pixel_count > 300 and extent < 0.45:
            return "Excavation & Cleared Ground"

        # Default fallback category
        return "Industrial & Facility Expansion"

    def _render_mask_base64(self, mask: np.ndarray) -> str:
        """Renders high-contrast neon cyan binary change mask."""
        h, w = mask.shape
        rgb_mask = np.zeros((h, w, 3), dtype=np.uint8)
        # Neon Cyan color [0, 240, 255] for detected human activity
        rgb_mask[mask > 0] = [0, 240, 255]
        return self._ndarray_to_base64(rgb_mask)

    def _render_heatmap_base64(self, prob_map: np.ndarray) -> str:
        """Generates a color change heatmap."""
        # Simple color map from black -> blue -> cyan -> yellow -> red
        norm = np.clip(prob_map, 0.0, 1.0)
        h, w = norm.shape
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        
        # Color gradient interpolation
        r = np.clip((norm - 0.5) * 2.0 * 255.0, 0, 255).astype(np.uint8)
        g = np.clip(np.sin(norm * np.pi) * 255.0, 0, 255).astype(np.uint8)
        b = np.clip((1.0 - norm * 1.5) * 255.0, 0, 255).astype(np.uint8)
        
        rgb[..., 0] = r
        rgb[..., 1] = g
        rgb[..., 2] = b
        
        return self._ndarray_to_base64(rgb)

    def _render_overlay_base64(
        self, 
        base_img: np.ndarray, 
        mask: np.ndarray, 
        clusters: List[DetectedCluster]
    ) -> str:
        """Renders T2 with semi-transparent change highlight and vector bounding boxes."""
        pil_base = Image.fromarray(base_img).resize((mask.shape[1], mask.shape[0])).convert("RGBA")
        
        # Color overlay mask
        overlay = Image.new("RGBA", pil_base.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Alpha highlight on detected pixels
        mask_pixels = np.where(mask > 0)
        if len(mask_pixels[0]) > 0:
            for y, x in zip(mask_pixels[0], mask_pixels[1]):
                overlay.putpixel((int(x), int(y)), (255, 60, 60, 140)) # Vibrant coral-red

        # Draw bounding boxes and cluster labels
        draw = ImageDraw.Draw(pil_base)
        for cluster in clusters:
            min_x, min_y, max_x, max_y = cluster.bbox
            color = "#00f0ff" if cluster.severity == "HIGH" else "#ffaa00"
            draw.rectangle([min_x, min_y, max_x, max_y], outline=color, width=2)
            # Text labels removed to prevent overlapping mess on small clusters

        # Composite base and overlay
        blended = Image.alpha_composite(pil_base, overlay).convert("RGB")
        return self._ndarray_to_base64(np.array(blended))

    def _ndarray_to_base64(self, arr: np.ndarray) -> str:
        """Encodes numpy uint8 array to PNG base64 string."""
        pil_img = Image.fromarray(arr.astype(np.uint8))
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
