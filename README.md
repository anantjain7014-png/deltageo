# DeltaGeo (by Team Vertex Dynasty)

## Project Overview

DeltaGeo is an advanced AI-powered bi-temporal remote sensing platform engineered to automatically detect, classify, and visualize anthropogenic changes across satellite imagery. By utilizing deep learning and high-resolution data from Sentinel-2 and LISS-4, the system empowers analysts and urban planners to monitor critical infrastructure development and human activity with unparalleled precision.

## Problem Statement (SIH1518)
**Change Detection Due to Human Activities**

## Description
Using satellite imagery, create an automated system for detecting change related only to human activities from satellite imagery, i.e. develop an AI/ML-based model for change detection of only man-made objects like vehicles, buildings, roads, aircraft, etc. from remote sensing images. Data: Sentinel-2, LISS-4.

## Objective
To build a highly accurate, sensor-agnostic model that filters out natural seasonal variations (like vegetation growth) to isolate real infrastructure development, such as new buildings, roads, industrial facilities, and excavations.

## Technology Stack

### Backend Technologies & Libraries
* Python 3
* FastAPI (High-performance API framework)
* Uvicorn (ASGI web server)
* Pydantic (Data validation and schemas)
* ReportLab (PDF report generation)

### Artificial Intelligence & Computer Vision
* TensorFlow / Keras (Deep Learning Framework)
* Siamese U-Net Architecture (For Bi-temporal feature extraction)
* OpenCV (cv2) (Image manipulation and preprocessing)
* NumPy (High-performance array operations)
* SciPy (N-dimensional image processing and morphological operations)
* Scikit-Image (skimage) (Connected component analysis and region property extraction)
* Pillow (PIL) (Image decoding and format management)

### Frontend Technologies
* HTML5 (Semantic Structure)
* CSS3 (Vanilla Custom Light Theme, CSS Grid/Flexbox)
* JavaScript (ES6+ Vanilla JS, asynchronous Fetch API)
* Chart.js (Data visualization and pie charts)
* GeoJSON Standard (For GIS data export)

## Project Structure

```text
DeltaGeo/
│
├── backend/                  # FastAPI Python Server
│   ├── app/
│   │   ├── api/              # API Routes (endpoints.py)
│   │   ├── core/             # Configuration settings
│   │   ├── schemas/          # Pydantic data models
│   │   └── services/         # Core AI logic (model_service.py, postprocessor.py)
│   └── samples/              # Pre-loaded benchmark image pairs
│
├── frontend/                 # Vanilla JS/CSS Dashboard
│   ├── landing.html          # Landing Page
│   ├── index.html            # Main UI Dashboard
│   ├── css/                  # Styling (style.css)
│   └── js/                   # UI logic (app.js, viewer.js, charts.js, api.js)
│
├── venv/                     # Python Virtual Environment
├── requirements.txt          # Python dependencies
├── run.py                    # Uvicorn entry point
└── start.bat                 # 1-Click Windows Startup Script
```

## Key Features

* Bi-Temporal Analysis: Upload "Before" (T1) and "After" (T2) satellite images to instantly detect changes.
* Siamese U-Net AI Engine: Utilizes a deep learning dual-encoder model (or a robust algorithmic fallback engine) for pixel-perfect change detection.
* Smart Filtering: Automatically suppresses false positives caused by natural phenological changes (e.g., seasons changing, grass drying) or cloud drift.
* Interactive Dashboard: 
  * Split Slider: Visually compare T1 and T2 images dynamically.
  * Vector Overlays: See bounding boxes around specific detected activities.
  * Heatmaps: View the AI's confidence map.
* Classification: Categorizes changes into specific types (e.g., Road & Pavement Infrastructure, Building & Urban Construction, Excavation).
* Export Ready: Instantly generate GeoJSON for professional GIS software (QGIS/ArcGIS/Bhuvan) or download automated PDF Audit Reports.
* Sensor Agnostic: Optimized for Sentinel-2 MSI (10m), ISRO LISS-4 (5.8m), and Cartosat High-Res imagery.

## How to Run Locally

### 1. The Easy Way (Windows)
If you are on Windows and the virtual environment is already set up, simply double-click the `start.bat` file in the root directory. 
This will automatically activate the environment, start the server, and open your browser.

### 2. The Manual Way (Terminal)
If you need to start the project manually from a terminal:

Step 1: Open your terminal and navigate to the project folder.
```bash
cd Vertex-Dynasty-DeltaGeo
```

Step 2: Place the AI Model File
Download the `best_siamese_unet_model.keras` file (if you haven't already) and place it directly in the root folder of this project (right next to `run.py`).

Step 3: Create and Activate the Python virtual environment.
* On Windows:
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```
* On Mac/Linux:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

Step 4: Install dependencies.
```bash
pip install -r requirements.txt
```

Step 5: Start the FastAPI backend server.
```bash
python run.py
```

Step 6: Access the App.
Open your web browser and go to: http://localhost:8080
```
