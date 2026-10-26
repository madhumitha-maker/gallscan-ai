import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.db.database import engine, Base
import app.db.models  # register ORM models
from app.inference.onnx_infer import get_onnx_predictor
from app.routers import health, auth, users, predict, history, notifications

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Verify database connection strictly (fail loud if down)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[DATABASE] Successfully connected to PostgreSQL / Neon DB.")
        Base.metadata.create_all(bind=engine)
        print("[DATABASE] Tables verified / created successfully.")
    except Exception as e:
        print(f"[FATAL ERROR] Database connection failed: {e}")
        raise RuntimeError(f"Database connection error on startup: {e}")

    # Warm up ONNX model session
    try:
        predictor = get_onnx_predictor()
        print(f"ONNX Model successfully loaded from {settings.ONNX_MODEL_PATH}")
    except Exception as e:
        print(f"Warning loading ONNX model: {e}")

    yield
    # Shutdown logic if needed

app = FastAPI(
    title="GallScan AI — Gallbladder Diagnostic & Explainability API",
    description="Multimodal CNN+ViT Deep Learning API for Automated Gallbladder Disease Detection and Grad-CAM Visual Heatmaps",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for scan uploads & Grad-CAM images
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOADS_DIR)), name="uploads")

# Also mount frontend directory if it exists to allow serving the complete full-stack app from port 8000
FRONTEND_DIR = settings.ROOT_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/client", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# Include Routers
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(predict.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "status": "operational",
        "docs_url": "/docs",
        "health_check": "/api/health",
        "disclaimer": settings.CLINICAL_DISCLAIMER
    }
