/**
 * GallScan AI — Diagnostic Result & Grad-CAM Visualizer
 */

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const scanId = urlParams.get("id");

  if (!scanId) {
    window.location.href = "upload.html";
    return;
  }

  await loadResultData(scanId);
  initGradCAMControls();
});

async function loadResultData(scanId) {
  const loadingEl = document.getElementById("resultLoading");
  const contentEl = document.getElementById("resultContent");

  let data = null;

  try {
    data = await API.getPredictionById(scanId);
  } catch (err) {
    if (loadingEl) {
      loadingEl.innerHTML = `
        <div class="alert alert-error" style="max-width: 600px; margin: 40px auto;">
          <span class="material-symbols-outlined">error</span>
          <div>
            <strong>Error loading scan results from database:</strong><br>${err.message}
            <div style="margin-top: 12px;">
              <a href="upload.html" class="btn btn-primary btn-sm">Upload New Scan</a>
              <a href="history.html" class="btn btn-outline btn-sm">View History</a>
            </div>
          </div>
        </div>
      `;
    }
    return;
  }

  renderResult(data);
  if (loadingEl) loadingEl.style.display = "none";
  if (contentEl) contentEl.style.display = "block";
}

function renderResult(data) {
  // Filename & date
  const filenameEl = document.getElementById("resultFilename");
  const dateEl = document.getElementById("resultDate");
  const topClassEl = document.getElementById("resultTopClass");
  const topConfEl = document.getElementById("resultTopConfidence");
  const topBadgeEl = document.getElementById("resultTopBadge");

  if (filenameEl) filenameEl.textContent = data.filename;
  if (dateEl) {
    const d = new Date(data.created_at || Date.now());
    dateEl.textContent = d.toLocaleString();
  }

  // Top diagnosis
  const topDisplay = data.predicted_display_name || data.predicted_class;
  const confVal = data.confidence || (data.top_3_predictions && data.top_3_predictions[0] ? data.top_3_predictions[0].probability : 0);
  const confPct = (confVal * 100).toFixed(1);

  if (topClassEl) topClassEl.textContent = topDisplay;
  if (topConfEl) topConfEl.textContent = `${confPct}% Confidence`;
  if (topBadgeEl) {
    if (confVal > 0.8) {
      topBadgeEl.className = "badge badge-teal";
      topBadgeEl.textContent = "High Confidence (Primary Match)";
    } else if (confVal > 0.5) {
      topBadgeEl.className = "badge badge-warning";
      topBadgeEl.textContent = "Moderate Confidence (Differential Alert)";
    } else {
      topBadgeEl.className = "badge badge-danger";
      topBadgeEl.textContent = "Equivocal / Low Confidence";
    }
  }

  // Top-3 differential predictions
  const top3ListEl = document.getElementById("top3PredictionsList");
  if (top3ListEl && data.top_3_predictions) {
    top3ListEl.innerHTML = data.top_3_predictions.map((item, idx) => {
      const barClass = idx === 0 ? "high" : (item.percentage > 25 ? "warning" : "");
      return `
        <div style="margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="badge ${idx === 0 ? 'badge-navy' : 'badge-teal'}">#${idx + 1}</span>
              <span style="font-size: 13px; font-weight: 600; color: var(--primary-navy);">${item.display_name}</span>
            </div>
            <span class="mono-text" style="font-size: 13px; font-weight: 700; color: var(--primary-navy);">${item.percentage}%</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill ${barClass}" style="width: ${item.percentage}%;"></div>
          </div>
        </div>
      `;
    }).join("");
  }

  // Images
  const origImg = document.getElementById("resultOrigImg");
  const gradcamImg = document.getElementById("resultGradcamImg");
  const overlayHeatmapImg = document.getElementById("overlayHeatmapImg");

  const origUrl = data.original_image_url ? `${API_BASE}${data.original_image_url}` : "";
  const camUrl = data.gradcam_image_url ? `${API_BASE}${data.gradcam_image_url}` : "";

  if (origImg) origImg.src = origUrl;
  if (gradcamImg) gradcamImg.src = camUrl;
  if (overlayHeatmapImg) overlayHeatmapImg.src = camUrl;

  // 9-class breakdown table
  const fullTableBody = document.getElementById("fullClassTableBody");
  if (fullTableBody && data.class_probabilities) {
    const entries = Object.entries(data.class_probabilities)
      .map(([raw, prob]) => ({
        raw,
        prob: Number(prob),
        pct: (Number(prob) * 100).toFixed(2)
      }))
      .sort((a, b) => b.prob - a.prob);

    fullTableBody.innerHTML = entries.map(item => `
      <tr>
        <td style="font-weight: 500;">${window.DISPLAY_MAP ? window.DISPLAY_MAP[item.raw] || item.raw : item.raw}</td>
        <td class="mono-text" style="text-align: right; font-weight: 600;">${item.pct}%</td>
        <td style="width: 140px;">
          <div class="progress-track">
            <div class="progress-fill" style="width: ${item.pct}%;"></div>
          </div>
        </td>
      </tr>
    `).join("");
  }
}

function initGradCAMControls() {
  const modeSideBySideBtn = document.getElementById("modeSideBySide");
  const modeOverlayBtn = document.getElementById("modeOverlay");
  const viewSideBySide = document.getElementById("viewSideBySide");
  const viewOverlay = document.getElementById("viewOverlay");
  const opacitySlider = document.getElementById("heatmapOpacitySlider");
  const opacityValEl = document.getElementById("opacityVal");
  const overlayHeatmapImg = document.getElementById("overlayHeatmapImg");

  if (modeSideBySideBtn && modeOverlayBtn) {
    modeSideBySideBtn.addEventListener("click", () => {
      modeSideBySideBtn.classList.add("btn-primary");
      modeSideBySideBtn.classList.remove("btn-outline");
      modeOverlayBtn.classList.remove("btn-primary");
      modeOverlayBtn.classList.add("btn-outline");
      if (viewSideBySide) viewSideBySide.style.display = "grid";
      if (viewOverlay) viewOverlay.style.display = "none";
    });

    modeOverlayBtn.addEventListener("click", () => {
      modeOverlayBtn.classList.add("btn-primary");
      modeOverlayBtn.classList.remove("btn-outline");
      modeSideBySideBtn.classList.remove("btn-primary");
      modeSideBySideBtn.classList.add("btn-outline");
      if (viewSideBySide) viewSideBySide.style.display = "none";
      if (viewOverlay) viewOverlay.style.display = "flex";
    });
  }

  if (opacitySlider && overlayHeatmapImg) {
    opacitySlider.addEventListener("input", (e) => {
      const val = e.target.value;
      if (opacityValEl) opacityValEl.textContent = `${val}%`;
      overlayHeatmapImg.style.opacity = val / 100;
    });
  }

  // Print button
  const printBtn = document.getElementById("btnPrintReport");
  if (printBtn) {
    printBtn.addEventListener("click", () => {
      window.print();
    });
  }
}
