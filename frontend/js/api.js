const API = {
  baseUrl: "/api/v1",

  async getHealth() {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) throw new Error("Failed to check health");
    return await res.json();
  },

  async getModelInfo() {
    const res = await fetch(`${this.baseUrl}/model-info`);
    if (!res.ok) throw new Error("Failed to fetch model info");
    return await res.json();
  },

  async getSamples() {
    const res = await fetch(`${this.baseUrl}/samples`);
    if (!res.ok) throw new Error("Failed to fetch sample datasets");
    return await res.json();
  },

  async detectChanges(formData) {
    const res = await fetch(`${this.baseUrl}/detect`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Inference failed" }));
      throw new Error(err.detail || "Inference failed");
    }
    return await res.json();
  },

  async detectSample(sampleId, params = {}) {
    const url = new URL(`${window.location.origin}${this.baseUrl}/detect-sample/${sampleId}`);
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));
    
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Sample analysis failed" }));
      throw new Error(err.detail || "Sample analysis failed");
    }
    return await res.json();
  },

  async exportGeoJSON(detectionData) {
    const res = await fetch(`${this.baseUrl}/export/geojson`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(detectionData),
    });
    if (!res.ok) throw new Error("Failed to generate GeoJSON");
    return await res.json();
  },

  async downloadPDFReport(detectionData) {
    const res = await fetch(`${this.baseUrl}/export/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(detectionData),
    });
    if (!res.ok) throw new Error("Failed to generate PDF report");
    return await res.blob();
  }
};
