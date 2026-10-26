/**
 * GallScan AI — Scan Upload & Pre-analysis Handler
 */

document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const previewContainer = document.getElementById("previewContainer");
  const previewImg = document.getElementById("previewImg");
  const fileNameEl = document.getElementById("previewFileName");
  const fileSizeEl = document.getElementById("previewFileSize");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const uploadForm = document.getElementById("uploadForm");
  const submitBtn = document.getElementById("submitUploadBtn");
  const uploadAlert = document.getElementById("uploadAlert");
  const uploadProgress = document.getElementById("uploadProgress");

  let selectedFile = null;

  if (!dropZone || !fileInput) return;

  // Drop zone events
  ["dragenter", "dragover"].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.style.borderColor = "var(--accent-cyan)";
      dropZone.style.backgroundColor = "var(--secondary-teal-light)";
    });
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.style.borderColor = "var(--border-light)";
      dropZone.style.backgroundColor = "var(--surface-lowest)";
    });
  });

  dropZone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  if (removeFileBtn) {
    removeFileBtn.addEventListener("click", () => {
      selectedFile = null;
      fileInput.value = "";
      previewContainer.style.display = "none";
      dropZone.style.display = "block";
      if (submitBtn) submitBtn.disabled = true;
    });
  }

  function handleFileSelection(file) {
    const validExtensions = ["image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"];
    if (!validExtensions.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|webp|bmp|tif|tiff)$/i)) {
      showAlert("Invalid file format. Please upload a standard radiological ultrasound image (.png, .jpg, .webp).");
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      showAlert("File size exceeds 20MB limit. Please provide a lighter radiological scan.");
      return;
    }

    selectedFile = file;
    if (uploadAlert) uploadAlert.style.display = "none";

    // Read and display preview
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      fileNameEl.textContent = file.name;
      fileSizeEl.textContent = `${(file.size / 1024).toFixed(1)} KB`;
      dropZone.style.display = "none";
      previewContainer.style.display = "block";
      if (submitBtn) submitBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  function showAlert(msg) {
    if (uploadAlert) {
      uploadAlert.textContent = msg;
      uploadAlert.style.display = "flex";
    }
  }

  // Form submission
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!selectedFile) {
        showAlert("Please select a gallbladder ultrasound scan before proceeding.");
        return;
      }

      const notesInput = document.getElementById("scanNotes");
      const notes = notesInput ? notesInput.value.trim() : "";

      const formData = new FormData();
      formData.append("file", selectedFile);
      if (notes) formData.append("notes", notes);

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="material-symbols-outlined" style="animation: spin 1s linear infinite;">sync</span> Running CNN+ViT Inference...`;
      if (uploadProgress) uploadProgress.style.display = "block";
      if (uploadAlert) uploadAlert.style.display = "none";

      try {
        const result = await API.predict(formData);
        // Direct navigation to result page, which will load from PostgreSQL via API
        window.location.href = `result.html?id=${result.id}`;
      } catch (err) {
        showAlert(err.message || "Failed to process scan. Ensure the backend is reachable.");
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<span class="material-symbols-outlined">analytics</span> Run Multimodal Analysis`;
        if (uploadProgress) uploadProgress.style.display = "none";
      }
    });
  }
});
