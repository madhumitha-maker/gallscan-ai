# Project Handoff — Gallbladder Disease Classifier: Full-Stack App

Paste this document into Antigravity (or a new chat) to continue building the application. It captures everything decided so far so context isn't rediscovered from scratch.

---

## 1. Where this project stands

**Title:** An Explainable Deep Learning-Based Multimodal System for Automated Detection and Classification of Gallbladder Diseases from Radiological Scans

**Completed — model:** Trained a CNN+ViT fusion model (EfficientNet-B0 + ViT-Small via `timm`) on the Mendeley Gallbladder Diseases Dataset v2 (ultrasound, 9 classes, ~10,692 images) in Google Colab. Training, evaluation (accuracy/sensitivity/specificity/precision/F1/AUC), and Grad-CAM explainability are done. Final export zip downloaded successfully — see Section 2 for how it's split between runtime and report use.

**Completed — UI design:** All application screens designed in Stitch:
- Upload, Result, History (core prediction flow)
- Landing page
- Auth: Login, Sign Up, Forgot Password
- Profile page
- Notifications: header popover + full Notification Center page

Project named `GallScanAI` in Stitch, so Antigravity's Stitch MCP integration can fetch its Design DNA by that name.

**Scope note carried over:** dataset is ultrasound-only; the CNN+ViT fusion is the practical stand-in for "multimodal," architecture is designed to be extensible to CT/MRCP later. Keep this framing consistent in the app's UI copy and any report — don't imply the deployed app accepts CT/MRCP today.

**Stack decided:**
- **Frontend:** HTML, CSS, JS — screens designed in Stitch, implemented in Antigravity via Stitch MCP
- **Backend:** FastAPI
- **Database:** PostgreSQL
- **Inference:** `onnxruntime` for prediction; PyTorch (`model_weights.pt` + `CNNViTFusion` class) for live per-upload Grad-CAM
- **Auth:** now in scope — email/password with JWT (see Section 3)

---

## 2. Exported Colab zip — what goes where

The zip is a **build artifact**, not source code, and never touches the database directly — it's loaded once at FastAPI startup and reused for every request.

```
export/                          (as downloaded from Colab)
├── model_weights.pt          ─┐
├── model.onnx                 │  → copy into backend/artifacts/ (runtime files)
├── class_mapping.json         │
├── preprocessing_config.json ─┘
├── training_curves.png       ─┐
├── confusion_matrix.png       │  → move into docs/training_artifacts/ (report/thesis evidence, not loaded by the app)
├── gradcam_samples.png        │
└── test_metrics.csv          ─┘
```

- Only the four runtime files live under `backend/artifacts/`.
- The other four are evidence for your write-up — keep them in the repo under `docs/training_artifacts/` so they're versioned alongside the code, but the app never reads them.
- Preprocessing at inference time **must exactly match** `preprocessing_config.json` (resize, RGB, ImageNet normalization) or predictions will be silently wrong — no error, just bad output.
- The `CNNViTFusion` class definition used for live Grad-CAM must be copied in verbatim from training, not reimplemented from memory.

---

## 3. Auth — now in scope

Single-user/no-auth was the original default; adding Profile + per-user History reverses that. Concretely this means:

- **New DB table `users`:** id, name, email (unique), password_hash, created_at.
- **`predictions` table gets a `user_id` FK** — history becomes per-user, not global.
- **New DB table `notifications`:** id, user_id (FK), message, type, is_read, created_at — needed because the Notification Center design shows persisted, groupable-by-date notifications, not just ephemeral toasts.
- **Backend auth:** JWT-based (e.g. `fastapi-users` or a hand-rolled flow), password hashing via `passlib`/`bcrypt`, protected routes for `/predict`, `/history`, `/users/me`, `/notifications`.
- **Password reset:** minimal flow — email field → reset link → confirmation state, matching the Stitch design. Actual email delivery can be stubbed/logged for the demo unless sending real email is part of your scope.

---

## 4. Suggested FastAPI endpoints (updated)

```
POST   /auth/signup
POST   /auth/login
POST   /auth/forgot-password
POST   /auth/reset-password

GET    /users/me                # profile data + summary stats (total scans, most recent scan date)
PATCH  /users/me                # edit name/email
POST   /users/me/change-password

POST   /predict                 # protected — returns {predicted_class, confidence, class_probabilities, gradcam_image, disclaimer}
GET    /history                 # protected, paginated, filterable by class — scoped to current user
GET    /history/{id}            # protected — single record with stored Grad-CAM image

GET    /notifications           # protected, grouped by date
PATCH  /notifications/{id}/read
PATCH  /notifications/read-all

GET    /health                  # liveness + model-loaded check, unauthenticated
```

---

## 5. Suggested PostgreSQL schema (updated)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    filename TEXT NOT NULL,
    predicted_class TEXT NOT NULL,
    confidence REAL NOT NULL,
    class_probabilities JSONB NOT NULL,   -- {class_name: prob, ...}
    gradcam_image_path TEXT,               -- or store in object storage, keep path/URL only
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    type TEXT,                             -- e.g. 'analysis_complete', 'gradcam_ready'
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 6. File structure (updated)

```
gallbladder-app/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, route registration
│   │   ├── routers/
│   │   │   ├── auth.py              # /auth/signup, /login, /forgot-password, /reset-password
│   │   │   ├── users.py             # /users/me (profile, stats, edit, change-password)
│   │   │   ├── predict.py           # POST /predict
│   │   │   ├── history.py           # GET /history, /history/{id}
│   │   │   ├── notifications.py     # /notifications, /notifications/{id}/read
│   │   │   └── health.py            # GET /health
│   │   ├── models/
│   │   │   ├── fusion_model.py      # CNNViTFusion class def (copied verbatim)
│   │   │   └── schemas.py           # Pydantic request/response models
│   │   ├── inference/
│   │   │   ├── onnx_infer.py        # onnxruntime prediction path
│   │   │   └── gradcam.py           # live Grad-CAM via PyTorch
│   │   ├── auth/
│   │   │   ├── security.py          # password hashing, JWT create/verify
│   │   │   └── dependencies.py      # get_current_user, etc.
│   │   ├── db/
│   │   │   ├── database.py          # SQLAlchemy engine/session
│   │   │   ├── models.py            # ORM: users, predictions, notifications
│   │   │   └── crud.py
│   │   └── config.py                # paths, preprocessing_config.json loader
│   ├── artifacts/                   # model_weights.pt, model.onnx, class_mapping.json, preprocessing_config.json
│   ├── requirements.txt
│   └── alembic/                     # DB migrations
├── frontend/
│   ├── index.html                   # landing page
│   ├── login.html
│   ├── signup.html
│   ├── forgot-password.html
│   ├── upload.html
│   ├── result.html
│   ├── history.html
│   ├── profile.html
│   ├── notifications.html           # full Notification Center page
│   ├── css/
│   ├── js/
│   │   ├── api.js                   # fetch calls to FastAPI
│   │   ├── auth.js
│   │   ├── upload.js
│   │   ├── history.js
│   │   ├── profile.js
│   │   └── notifications.js         # header popover + center page logic
│   └── assets/
├── docs/
│   └── training_artifacts/          # training_curves.png, confusion_matrix.png, gradcam_samples.png, test_metrics.csv
├── docker-compose.yml                # postgres + backend, for local dev
├── .env.example
└── README.md
```

---

## 7. Non-negotiable disclaimer

This is an academic/demo project, not a diagnostic device. The frontend must display a visible disclaimer (result screen banner + persistent footer) stating the tool is for research/educational purposes and not a substitute for professional medical diagnosis. It's also baked into the `/predict` response payload as a `disclaimer` field.

---

## 8. Recommended build order

1. Backend skeleton: FastAPI app, `/health`, DB connection, `users`/`predictions`/`notifications` tables via Alembic migration.
2. Auth: signup/login/JWT, protected route dependency.
3. `/predict` using `onnxruntime`, tested locally with a sample image before touching the DB.
4. Wire `/predict` to persist a record; add live Grad-CAM path.
5. `/history`, `/users/me`, `/notifications` endpoints.
6. In Antigravity: connect Stitch MCP, fetch Design DNA for all 7 screens, scaffold `frontend/` against the structure above.
7. Wire frontend to live backend, screen by screen: auth → landing → upload/result → history → profile → notifications.
8. Packaging/deployment instructions once everything works locally.

---

## 9. Known constraints from the training phase (carry forward)

- Preprocessing at inference time must exactly match `preprocessing_config.json` — see Section 2.
- Live Grad-CAM requires the exact `CNNViTFusion` class definition from training.
- Confusion between clinically similar classes (e.g., cholecystitis vs. membranous/gangrenous cholecystitis) was observed during evaluation — the Result screen surfaces top-3 predictions rather than only top-1 to keep this ambiguity visible.
