import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from backend.app.core.config import SAMPLES_DIR


def create_sample_datasets():
    # Base canvas size 256x256
    size = (256, 256)
    
    # ----------------------------------------------------
    # Pair 1: Urban Expansion (Building Construction) - Sentinel-2
    # ----------------------------------------------------
    # T1: Rural landscape with green patches and dirt tracks
    np.random.seed(42)
    t1_arr = np.zeros((256, 256, 3), dtype=np.uint8)
    t1_arr[..., 0] = np.random.randint(60, 95, (256, 256))   # R
    t1_arr[..., 1] = np.random.randint(110, 160, (256, 256)) # G (Vegetation)
    t1_arr[..., 2] = np.random.randint(40, 75, (256, 256))   # B
    
    img_t1 = Image.fromarray(t1_arr).filter(ImageFilter.GaussianBlur(1.2))
    draw_t1 = ImageDraw.Draw(img_t1)
    # Existing dirt trail
    draw_t1.line([(10, 50), (120, 90), (240, 150)], fill=(160, 140, 110), width=3)
    
    # T2: Multiple new concrete rectangular buildings + asphalt access road
    img_t2 = img_t1.copy()
    draw_t2 = ImageDraw.Draw(img_t2)
    # New paved asphalt road
    draw_t2.line([(10, 50), (120, 90), (240, 150)], fill=(65, 70, 75), width=7)
    # Building 1 (New Commercial Complex)
    draw_t2.rectangle([45, 110, 105, 175], fill=(220, 225, 235), outline=(130, 140, 155), width=2)
    draw_t2.rectangle([55, 120, 95, 165], fill=(180, 190, 205))
    # Building 2 (Residential Block)
    draw_t2.rectangle([135, 30, 210, 85], fill=(235, 215, 200), outline=(150, 130, 120), width=2)
    # Building 3 (Facility Warehouse)
    draw_t2.rectangle([150, 170, 230, 230], fill=(200, 220, 240), outline=(100, 120, 150), width=2)
    # Cleared surrounding ground
    draw_t2.rectangle([35, 100, 115, 185], outline=(170, 155, 130), width=1)
    
    img_t1.save(SAMPLES_DIR / "urban_expansion_t1.png")
    img_t2.save(SAMPLES_DIR / "urban_expansion_t2.png")

    # ----------------------------------------------------
    # Pair 2: Highway & Road Infrastructure - LISS-4
    # ----------------------------------------------------
    # T1: Forest/Farmland terrain
    np.random.seed(101)
    t1_arr2 = np.zeros((256, 256, 3), dtype=np.uint8)
    t1_arr2[..., 0] = np.random.randint(70, 110, (256, 256))
    t1_arr2[..., 1] = np.random.randint(120, 170, (256, 256))
    t1_arr2[..., 2] = np.random.randint(50, 80, (256, 256))
    img_t1_road = Image.fromarray(t1_arr2).filter(ImageFilter.GaussianBlur(1.0))
    
    # T2: New dual-carriageway highway carved through terrain + overpass
    img_t2_road = img_t1_road.copy()
    draw_t2_road = ImageDraw.Draw(img_t2_road)
    # Broad highway corridor (cleared buffer)
    draw_t2_road.line([(0, 128), (256, 128)], fill=(185, 170, 140), width=24)
    # Paved asphalt twin lanes
    draw_t2_road.line([(0, 123), (256, 123)], fill=(50, 52, 58), width=6)
    draw_t2_road.line([(0, 133), (256, 133)], fill=(50, 52, 58), width=6)
    # Highway interchange ramp
    draw_t2_road.arc([80, 70, 180, 190], start=0, end=180, fill=(50, 52, 58), width=5)
    # Logistics vehicles / trucks
    draw_t2_road.rectangle([60, 121, 74, 125], fill=(240, 240, 240))
    draw_t2_road.rectangle([190, 131, 204, 135], fill=(230, 190, 40))
    
    img_t1_road.save(SAMPLES_DIR / "road_construction_t1.png")
    img_t2_road.save(SAMPLES_DIR / "road_construction_t2.png")

    # ----------------------------------------------------
    # Pair 3: Industrial Logistics & Facility Expansion - Optical
    # ----------------------------------------------------
    # T1: Open scrubland
    np.random.seed(202)
    t1_arr3 = np.zeros((256, 256, 3), dtype=np.uint8)
    t1_arr3[..., 0] = np.random.randint(140, 175, (256, 256)) # sandy/dry scrub
    t1_arr3[..., 1] = np.random.randint(130, 160, (256, 256))
    t1_arr3[..., 2] = np.random.randint(90, 120, (256, 256))
    img_t1_ind = Image.fromarray(t1_arr3).filter(ImageFilter.GaussianBlur(1.0))
    
    # T2: Large industrial plant + storage tanks + paved perimeter
    img_t2_ind = img_t1_ind.copy()
    draw_t2_ind = ImageDraw.Draw(img_t2_ind)
    # Paved apron
    draw_t2_ind.rectangle([30, 30, 226, 226], fill=(130, 135, 140), outline=(80, 85, 90), width=2)
    # Main Plant Hall
    draw_t2_ind.rectangle([50, 50, 160, 140], fill=(210, 225, 245), outline=(70, 100, 140), width=2)
    # Storage Silos / Tanks
    draw_t2_ind.ellipse([180, 50, 215, 85], fill=(240, 240, 245), outline=(120, 120, 130), width=2)
    draw_t2_ind.ellipse([180, 100, 215, 135], fill=(240, 240, 245), outline=(120, 120, 130), width=2)
    # Warehouse 2
    draw_t2_ind.rectangle([60, 160, 190, 210], fill=(230, 230, 230), outline=(100, 100, 100), width=2)
    
    img_t1_ind.save(SAMPLES_DIR / "industrial_facility_t1.png")
    img_t2_ind.save(SAMPLES_DIR / "industrial_facility_t2.png")

    print("All sample satellite pairs created successfully.")

if __name__ == "__main__":
    create_sample_datasets()
