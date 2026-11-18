class SatelliteViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.splitWrapper = document.getElementById("splitWrapper");
    this.imgBase = document.getElementById("imgBase");
    this.imgOverlay = document.getElementById("imgOverlay");
    this.overlayWrapper = document.getElementById("overlayWrapper");
    this.splitHandle = document.getElementById("splitHandle");

    this.currentMode = "split"; // 'split', 'side-by-side', 'overlay', 'mask', 'heatmap'
    this.zoomLevel = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.isDraggingSplit = false;
    this.isPanning = false;
    this.startX = 0;
    this.startY = 0;

    this.images = {
      t1: "",
      t2: "",
      overlay: "",
      mask: "",
      heatmap: ""
    };

    this.initEvents();
  }

  setImages(data) {
    this.images.t1 = data.t1_base64;
    this.images.t2 = data.t2_base64;
    this.images.overlay = data.overlay_base64;
    this.images.mask = data.mask_base64;
    this.images.heatmap = data.heatmap_base64;

    this.updateDisplayMode(this.currentMode);
  }

  updateDisplayMode(mode) {
    this.currentMode = mode;
    if (!this.imgBase || !this.imgOverlay) return;

    if (mode === "split") {
      this.overlayWrapper.style.display = "block";
      this.splitHandle.style.display = "flex";
      this.imgBase.src = this.images.overlay || this.images.t2;
      this.imgOverlay.src = this.images.t1;
      this.setSplitPosition(50);
    } else if (mode === "overlay") {
      this.overlayWrapper.style.display = "none";
      this.splitHandle.style.display = "none";
      this.imgBase.src = this.images.overlay || this.images.t2;
    } else if (mode === "mask") {
      this.overlayWrapper.style.display = "none";
      this.splitHandle.style.display = "none";
      this.imgBase.src = this.images.mask;
    } else if (mode === "heatmap") {
      this.overlayWrapper.style.display = "none";
      this.splitHandle.style.display = "none";
      this.imgBase.src = this.images.heatmap;
    } else if (mode === "raw_t1") {
      this.overlayWrapper.style.display = "none";
      this.splitHandle.style.display = "none";
      this.imgBase.src = this.images.t1;
    } else if (mode === "raw_t2") {
      this.overlayWrapper.style.display = "none";
      this.splitHandle.style.display = "none";
      this.imgBase.src = this.images.t2;
    }
  }

  setSplitPosition(percent) {
    const clamped = Math.max(0, Math.min(100, percent));
    if (this.overlayWrapper) this.overlayWrapper.style.width = `${clamped}%`;
    if (this.splitHandle) this.splitHandle.style.left = `${clamped}%`;

    // Ensure the inner overlay image matches the container width for 1:1 pixel alignment
    if (this.imgOverlay && this.container) {
      this.imgOverlay.style.width = `${this.container.clientWidth}px`;
    }
  }

  initEvents() {
    if (!this.container) return;

    // Handle split drag
    const onMouseDown = (e) => {
      if (this.currentMode !== "split") return;
      this.isDraggingSplit = true;
      e.preventDefault();
    };

    const onMouseMove = (e) => {
      if (this.isDraggingSplit) {
        const rect = this.container.getBoundingClientRect();
        const offsetX = e.clientX - rect.left;
        const percent = (offsetX / rect.width) * 100;
        this.setSplitPosition(percent);
      }
    };

    const onMouseUp = () => {
      this.isDraggingSplit = false;
    };

    // Touch support for mobile/tablets
    const onTouchMove = (e) => {
      if (this.isDraggingSplit && e.touches.length > 0) {
        const rect = this.container.getBoundingClientRect();
        const offsetX = e.touches[0].clientX - rect.left;
        const percent = (offsetX / rect.width) * 100;
        this.setSplitPosition(percent);
      }
    };

    if (this.splitHandle) {
      this.splitHandle.addEventListener("mousedown", onMouseDown);
      this.splitHandle.addEventListener("touchstart", onMouseDown);
    }
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    window.addEventListener("touchmove", onTouchMove);
    window.addEventListener("touchend", onMouseUp);

    // Zoom and pan controls
    this.container.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
      this.setZoom(this.zoomLevel * zoomFactor);
    }, { passive: false });

    // Handle window resize
    window.addEventListener("resize", () => {
      if (this.imgOverlay && this.container) {
        this.imgOverlay.style.width = `${this.container.clientWidth}px`;
      }
    });
  }

  setZoom(level) {
    this.zoomLevel = Math.max(0.5, Math.min(5.0, level));
    const transformStr = `scale(${this.zoomLevel}) translate(${this.panX}px, ${this.panY}px)`;
    if (this.imgBase) this.imgBase.style.transform = transformStr;
    if (this.imgOverlay) this.imgOverlay.style.transform = transformStr;
  }

  zoomIn() {
    this.setZoom(this.zoomLevel * 1.25);
  }

  zoomOut() {
    this.setZoom(this.zoomLevel * 0.8);
  }

  resetView() {
    this.zoomLevel = 1.0;
    this.panX = 0;
    this.panY = 0;
    this.setZoom(1.0);
    this.setSplitPosition(50);
  }
}
