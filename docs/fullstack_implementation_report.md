# GallScan AI — Full-Stack Implementation & System Report

**Project Title:** An Explainable Deep Learning-Based Multimodal System for Automated Detection and Classification of Gallbladder Diseases from Radiological Scans  
**Date:** August 30, 2026  
**Status:** Deployed, Fully Resolved & Verified with Neon PostgreSQL  

---

## 1. Executive Summary

The **GallScan AI Diagnostic Tool** is an end-to-end full-stack medical research platform that classifies gallbladder ultrasound scans into 9 radiological pathology classes. The system pairs rapid ONNX inference with live PyTorch Grad-CAM spatial activation heatmaps, backed by a persistent Neon PostgreSQL database, JWT authentication, and a Stitch-crafted Clinical Precision Narrative user interface.

```
                                 ┌──────────────────────────────┐
                                 │   Frontend (Stitch UI)       │
                                 │ HTML/CSS/JS (Port 8000)      │
                                 └──────────────┬───────────────┘
                                                │
                                                ▼ REST / JSON / Multipart
                                 ┌──────────────────────────────┐
                                 │   FastAPI Backend (Port 8000)│
                                 └───────┬──────────────┬───────┘
                                         │              │
                    ┌────────────────────┴──┐        ┌──┴───────────────────┐
                    ▼                       ▼        ▼                      ▼
           ┌────────────────┐      ┌─────────────┐ ┌────────────────┐ ┌──────────────┐
           │ ONNX Runtime   │      │ PyTorch     │ │ Neon PostgreSQL│ │ Uploads /    │
           │ (model.onnx)   │      │ (Grad-CAM)  │ │ (Remote DB)    │ │ Heatmaps     │
           └────────────────┘      └─────────────┘ └────────────────┘ └──────────────┘
```

---

## 2. Interface & Deployment Fixes Completed

All 4 issues requested in [`docs/gallscan_interface_fixes.md`](file:///d:/Projects/gallbladder-app/docs/gallscan_interface_fixes.md) have been resolved:

### Issue #1: Nav Bar Re-rendering / "Hopping" (Resolved)
- Extracted header and disclaimer into a single shared component: [`frontend/components/navbar.js`](file:///d:/Projects/gallbladder-app/frontend/components/navbar.js).
- Injected into `<div id="disclaimer-root"></div>` and `<div id="navbar-root"></div>` across all 7 pages.
- Standardized sticky navigation height (`68px`), layout container widths, and automatic active route detection (`home`, `upload`, `history`, `notifications`, `profile`).
- Eliminated all layout shifts and visual flickering across page transitions.

### Issue #2: Full Mobile Responsiveness (Resolved)
- Verified viewport meta tags (`width=device-width, initial-scale=1.0`) on every page.
- Added responsive breakpoints (`375px` iPhone SE, `768px` Tablet, `1024px` Desktop):
  - **Mobile Hamburger Drawer:** Replaces desktop nav on screens `< 768px` with slide-down drawer.
  - **Upload Screen:** 100% width responsive touch drop zone with min 44px touch targets.
  - **Result Screen:** Side-by-side scans and differential bar charts cleanly stack vertically on mobile.
  - **History Screen:** Automatically switches from standard table to stacked card items on mobile screens.
  - **Notification Popover:** Expands to full-width viewport card on mobile to prevent overflow.

### Issue #3: Vercel & Cloud Deployment Configuration (Resolved)
- Created [`vercel.json`](file:///d:/Projects/gallbladder-app/vercel.json) with clean URL routing for the static frontend and `/api` proxy rewrites.
- Created [`render.yaml`](file:///d:/Projects/gallbladder-app/render.yaml) for 1-click cloud deployment of the full PyTorch + Grad-CAM FastAPI backend with zero size limits.
- Configured dynamic `API_BASE` in [`frontend/js/api.js`](file:///d:/Projects/gallbladder-app/frontend/js/api.js) supporting custom cloud domains, Vercel proxy, or local development seamlessly.

### Issue #4: Removal of `sessionStorage` & Direct Neon PostgreSQL Persistence (Resolved)
- Audited all frontend JavaScript modules (`upload.js`, `result.js`, `history.js`, `profile.js`, `notifications.js`).
- Completely removed `sessionStorage` caching of predictions; `result.html` now always queries the live Neon PostgreSQL database via `/api/history/{id}`.
- Added fail-loud database connectivity check on backend startup in `main.py` (`SELECT 1`) to guarantee no silent in-memory fallbacks.

---

## 3. Live Application Endpoints

When running locally (`http://localhost:8000`):

| Page / Route | URL | Purpose |
| :--- | :--- | :--- |
| **Landing Page** | [`/client/index.html`](http://localhost:8000/client/index.html) | Architecture highlights, 9-class pathology taxonomy, disclaimer |
| **Scan Upload** | [`/client/upload.html`](http://localhost:8000/client/upload.html) | Drag-and-drop ultrasound image upload & pre-inference validation |
| **Diagnostic Results** | [`/client/result.html`](http://localhost:8000/client/result.html) | Top 3 differential diagnoses, Grad-CAM side-by-side & interactive overlay, PDF export |
| **Scan History** | [`/client/history.html`](http://localhost:8000/client/history.html) | Searchable, paginated archives filtered by disease class |
| **Notification Center** | [`/client/notifications.html`](http://localhost:8000/client/notifications.html) | Date-grouped activity stream with mark-as-read/delete |
| **Clinician Profile** | [`/client/profile.html`](http://localhost:8000/client/profile.html) | Account management, scan telemetry, and password updates |
| **Authentication** | [`/client/login.html`](http://localhost:8000/client/login.html) | Secure JWT login, registration, and password recovery |
| **Swagger API Docs** | [`/docs`](http://localhost:8000/docs) | Interactive FastAPI OpenAPI documentation explorer |
| **Health Check** | [`/api/health`](http://localhost:8000/api/health) | System health, model readiness, and clinical disclaimer |

---

## 4. Deep Learning & Inference Architecture

### 4.1 Model Backbone: CNN + Vision Transformer Fusion
- **CNN Branch:** `EfficientNet-B0` (1280-d spatial feature extraction via `conv_head`).
- **Transformer Branch:** `ViT-Small/16` (384-d global patch self-attention).
- **Fusion Layer:** Concatenation (1664-d) &rarr; `Linear(1664, 256)` &rarr; `BatchNorm1d(256)` &rarr; `ReLU` &rarr; `Dropout(0.3)`.
- **Classification Head:** `Linear(256, 9)`.

### 4.2 9 Gallbladder Pathology Classes (Mendeley v2)
1. **1Gallstones** — Cholelithiasis with acoustic shadowing.
2. **2Abdomen and retroperitoneum** — Normal/baseline parenchymal scans.
3. **3cholecystitis** — Acute/chronic mural inflammation & distension.
4. **4Membranous and gangrenous cholecystitis** — Ischemic wall necrosis & mucosal sloughing.
5. **5Perforation** — Wall disruption & pericholecystic effusion.
6. **6Polyps and cholesterol crystals** — Non-shadowing intraluminal projections.
7. **7Adenomyomatosis** — Mural thickening with Rokitansky-Aschoff sinuses.
8. **8Carcinoma** — Infiltrating/polypoid biliary malignancies.
9. **9Various causes of gallbladder wall thickening** — Non-specific reactive edema.

---

## 5. End-to-End Test Suite Verification

```text
==================================================
 GALLSCAN AI — FULL-STACK VERIFICATION TEST SUITE 
==================================================

[PASS] 1. Health Check:
       Status: healthy
       ONNX Loaded: True
       PyTorch Loaded: True
       Classes (9): ['1Gallstones', '2Abdomen and retroperitoneum', '3cholecystitis']...

[PASS] 2. User Authentication:
       User ID: 1
       Name: Dr. Sarah Jenkins, MD (sarah.jenkins@hospital.org)
       Role: radiologist

[PASS] 3. Scan Inference & Grad-CAM Generation:
       Prediction ID: #3
       Filename: patient_ultrasound_test.png
       Diagnosis: Gallbladder Carcinoma (Malignant)
       Confidence: 42.83%
       Top-3 Differential Diagnoses:
         - Gallbladder Carcinoma (Malignant): 42.83%
         - Gallbladder Perforation: 24.79%
         - Gangrenous / Membranous Cholecystitis: 7.69%
       Original Image URL: /uploads/scan_d4ec85efe4eb_orig.png
       Grad-CAM Heatmap URL: /uploads/scan_d4ec85efe4eb_gradcam.png

[PASS] 4. PostgreSQL Scan Archive History:
       Total Records in Neon DB: 2
       First Item Diagnosis: Gallbladder Carcinoma (Malignant)

[PASS] 5. Notification Activity Stream:
       Total Notifications: 3
       Unread Count: 3
       Latest Alert: Analysis Complete

[PASS] 6. Frontend Client Serving: HTTP 200 (Landing Page Available)

==================================================
 ALL 6 VERIFICATION TEST MODULES PASSED (100%)    
==================================================
```
