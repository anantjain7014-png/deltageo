let viewerInstance = null;
let chartsInstance = null;
let currentDetectionData = null;

let fileT1 = null;
let fileT2 = null;

document.addEventListener("DOMContentLoaded", async () => {
  viewerInstance = new SatelliteViewer("viewerContainer");
  chartsInstance = new SatelliteCharts();

  initDropzones();
  initControls();
  await loadModelInfo();
  await loadSampleGallery();

  // Auto-load first sample on start
  loadSampleById("urban_expansion");
});

async function loadModelInfo() {
  try {
    const info = await API.getModelInfo();
    const badge = document.getElementById("modelStatusBadge");
    if (badge) {
      badge.innerHTML = `<span class="pulse-dot"></span> AI Engine: Active (${info.architecture.split(' ')[0]})`;
    }
  } catch (err) {
    console.warn("Model info warning:", err);
  }
}

async function loadSampleGallery() {
  try {
    const samples = await API.getSamples();
    const container = document.getElementById("sampleGalleryContainer");
    if (!container) return;

    container.innerHTML = "";
    samples.forEach(sample => {
      const card = document.createElement("div");
      card.className = "col-md-4";
      card.innerHTML = `
        <div class="glass-card p-2 h-100 sample-item-card" style="cursor: pointer;" onclick="loadSampleById('${sample.id}')">
          <div class="d-flex align-items-center gap-2 mb-2">
            <span class="badge bg-primary text-wrap" style="font-size: 0.65rem;">${sample.sensor}</span>
            <small class="text-truncate fw-bold text-white">${sample.title}</small>
          </div>
          <div class="d-flex gap-1 mb-2">
            <img src="${sample.t1_thumb}" class="rounded" style="width: 48%; height: 60px; object-fit: cover;" alt="T1">
            <img src="${sample.t2_thumb}" class="rounded" style="width: 48%; height: 60px; object-fit: cover;" alt="T2">
          </div>
          <p class="text-muted small mb-0" style="font-size: 0.72rem; line-height: 1.2;">${sample.description.substring(0, 75)}...</p>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load sample gallery:", err);
  }
}

async function loadSampleById(sampleId) {
  showLoading(true, `Analyzing Benchmark Pair: ${sampleId.replace('_', ' ').toUpperCase()}...`);
  try {
    const threshold = parseFloat(document.getElementById("confidenceSlider").value) / 100.0;
    const filterNatural = document.getElementById("filterNaturalCheck").checked;
    
    const data = await API.detectSample(sampleId, {
      confidence_threshold: threshold,
      filter_natural_changes: filterNatural
    });

    renderResults(data);
  } catch (err) {
    alert("Sample analysis failed: " + err.message);
  } finally {
    showLoading(false);
  }
}

function initDropzones() {
  setupDropzone("dropzoneT1", "fileInputT1", "previewT1", (file) => { fileT1 = file; });
  setupDropzone("dropzoneT2", "fileInputT2", "previewT2", (file) => { fileT2 = file; });
}

function setupDropzone(zoneId, inputId, previewId, onFileSelected) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  const placeholder = zone.querySelector(".dropzone-placeholder");

  if (!zone || !input) return;

  zone.addEventListener("click", () => input.click());

  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("dragover");
  });

  zone.addEventListener("dragleave", () => {
    zone.classList.remove("dragover");
  });

  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  input.addEventListener("change", () => {
    if (input.files.length > 0) {
      handleFile(input.files[0]);
    }
  });

  function handleFile(file) {
    onFileSelected(file);
    const reader = new FileReader();
    reader.onload = (e) => {
      preview.src = e.target.result;
      preview.style.display = "block";
      if (placeholder) placeholder.style.display = "none";
    };
    reader.readAsDataURL(file);
  }
}

function initControls() {
  // Confidence slider update
  const slider = document.getElementById("confidenceSlider");
  const sliderVal = document.getElementById("confidenceValue");
  if (slider && sliderVal) {
    slider.addEventListener("input", () => {
      sliderVal.innerText = `${slider.value}%`;
    });
  }

  // Detect button trigger
  const runBtn = document.getElementById("runDetectBtn");
  if (runBtn) {
    runBtn.addEventListener("click", handleCustomUploadDetection);
  }

  // View mode switcher buttons
  document.querySelectorAll("[data-view-mode]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll("[data-view-mode]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const mode = btn.getAttribute("data-view-mode");
      if (viewerInstance) viewerInstance.updateDisplayMode(mode);
    });
  });

  // Zoom controls
  document.getElementById("btnZoomIn")?.addEventListener("click", () => viewerInstance?.zoomIn());
  document.getElementById("btnZoomOut")?.addEventListener("click", () => viewerInstance?.zoomOut());
  document.getElementById("btnResetView")?.addEventListener("click", () => viewerInstance?.resetView());

  // Export buttons
  document.getElementById("btnExportGeoJSON")?.addEventListener("click", exportGeoJSON);
  document.getElementById("btnExportPDF")?.addEventListener("click", exportPDFReport);
}

async function handleCustomUploadDetection() {
  if (!fileT1 || !fileT2) {
    alert("Please select or drop both T1 (Pre) and T2 (Post) satellite images.");
    return;
  }

  showLoading(true, "Executing Siamese U-Net Change Detection & Natural Filtering...");

  try {
    const formData = new FormData();
    formData.append("image_t1", fileT1);
    formData.append("image_t2", fileT2);
    formData.append("confidence_threshold", (parseFloat(document.getElementById("confidenceSlider").value) / 100.0).toString());
    formData.append("min_area_sq_meters", document.getElementById("minAreaInput").value);
    formData.append("filter_natural_changes", document.getElementById("filterNaturalCheck").checked.toString());
    formData.append("sensor_type", document.getElementById("sensorSelect").value);
    formData.append("resolution_meters", document.getElementById("resolutionSelect").value);

    const data = await API.detectChanges(formData);
    renderResults(data);
  } catch (err) {
    alert("Change Detection Error: " + err.message);
  } finally {
    showLoading(false);
  }
}

function renderResults(data) {
  currentDetectionData = data;
  if (!data || !data.metrics) return;

  // 1. Update Viewer
  if (viewerInstance) {
    viewerInstance.setImages(data);
  }

  // 2. Update KPI Metrics Cards
  document.getElementById("kpiTotalArea").innerText = `${data.metrics.total_change_area_sq_meters.toLocaleString()} m²`;
  document.getElementById("kpiHectares").innerText = `${data.metrics.total_change_area_hectares.toFixed(3)} ha`;
  document.getElementById("kpiChangePct").innerText = `${data.metrics.change_percentage.toFixed(2)}%`;
  document.getElementById("kpiClusterCount").innerText = `${data.metrics.total_clusters}`;
  document.getElementById("kpiDominant").innerText = data.metrics.dominant_activity;
  document.getElementById("kpiInferenceTime").innerText = `${data.metrics.processing_time_ms.toFixed(0)} ms`;

  // 3. Update Chart
  if (chartsInstance && data.metrics.class_distribution) {
    chartsInstance.renderHorizontalBarChart("horizontalBarChart", data.metrics.class_distribution, data.metrics.total_change_area_sq_meters);
    chartsInstance.renderDonutChart("changeBreakdownDonutChart", data.metrics.total_change_area_sq_meters, data.metrics.natural_filtered_area_sq_meters || 0);
  }
}



async function exportGeoJSON() {
  if (!currentDetectionData) {
    alert("Please run detection first.");
    return;
  }
  try {
    const geojson = await API.exportGeoJSON(currentDetectionData);
    const blob = new Blob([JSON.stringify(geojson, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Change_Map_${Date.now()}.geojson`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("GeoJSON export failed: " + err.message);
  }
}

async function exportPDFReport() {
  if (!currentDetectionData) {
    alert("Please run detection first.");
    return;
  }
  try {
    showLoading(true, "Compiling Analytical PDF Audit Report...");
    const blob = await API.downloadPDFReport(currentDetectionData);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Change_Detection_Report_${Date.now()}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("PDF report download failed: " + err.message);
  } finally {
    showLoading(false);
  }
}

function showLoading(show, message = "Processing satellite images...") {
  let overlay = document.getElementById("loadingOverlay");
  if (!overlay && show) {
    overlay = document.createElement("div");
    overlay.id = "loadingOverlay";
    overlay.className = "loading-overlay";
    overlay.innerHTML = `
      <div class="radar-spinner mb-3"></div>
    `;
    document.body.appendChild(overlay);
  } else if (overlay) {
    overlay.style.display = show ? "flex" : "none";
  }
}
