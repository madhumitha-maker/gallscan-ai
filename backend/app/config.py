import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

# Explicitly load .env from root directory if present
load_dotenv(ROOT_DIR / ".env")
load_dotenv(BASE_DIR / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "GallScan AI Diagnostic Tool"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "gallscan-ai-super-secret-jwt-key-2026-secure-token"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./gallscan.db")

    # Artifacts & Paths
    ROOT_DIR: Path = ROOT_DIR
    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    
    # Class mapping & preprocessing config paths
    CLASS_MAPPING_PATH: Path = BASE_DIR / "artifacts" / "class_mapping.json"
    PREPROCESSING_CONFIG_PATH: Path = BASE_DIR / "artifacts" / "preprocessing_config.json"
    ONNX_MODEL_PATH: Path = BASE_DIR / "artifacts" / "model.onnx"
    PYTORCH_WEIGHTS_PATH: Path = BASE_DIR / "artifacts" / "model_weights.pt"

    # Disclaimer
    CLINICAL_DISCLAIMER: str = (
        "GallScan AI is an investigational deep learning research platform designed for educational and "
        "decision-support exploration. It is not an FDA/CE-cleared diagnostic medical device and must not "
        "replace primary radiological evaluation, histopathology, or clinical judgment."
    )

    class Config:
        env_file = [str(ROOT_DIR / ".env"), str(BASE_DIR / ".env")]
        extra = "ignore"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)

# Load class mapping
class_mapping_file = settings.CLASS_MAPPING_PATH
if class_mapping_file.exists():
    with open(class_mapping_file, "r", encoding="utf-8") as f:
        _data = json.load(f)
        CLASS_NAMES = [v for k, v in sorted(_data["idx2label"].items(), key=lambda item: int(item[0]))]
        IDX_TO_LABEL = {int(k): v for k, v in _data["idx2label"].items()}
        LABEL_TO_IDX = _data.get("label2idx", {v: int(k) for k, v in _data["idx2label"].items()})
else:
    CLASS_NAMES = []
    IDX_TO_LABEL = {}
    LABEL_TO_IDX = {}

# Clean display names for UI
DISPLAY_NAMES = {
    "1Gallstones": "Gallstones (Cholelithiasis)",
    "2Abdomen and retroperitoneum": "Abdomen & Retroperitoneum (Normal/Non-target)",
    "3cholecystitis": "Cholecystitis (Acute/Chronic)",
    "4Membranous and gangrenous cholecystitis": "Gangrenous / Membranous Cholecystitis",
    "5Perforation": "Gallbladder Perforation",
    "6Polyps and cholesterol crystals": "Polyps & Cholesterol Crystals",
    "7Adenomyomatosis": "Gallbladder Adenomyomatosis",
    "8Carcinoma": "Gallbladder Carcinoma (Malignant)",
    "9Various causes of gallbladder wall thickening": "Non-specific Wall Thickening"
}

# Preprocessing configs
if settings.PREPROCESSING_CONFIG_PATH.exists():
    with open(settings.PREPROCESSING_CONFIG_PATH, "r", encoding="utf-8") as f:
        PREPROCESSING_CONFIG = json.load(f)
else:
    PREPROCESSING_CONFIG = {
        "img_size": 224,
        "normalize_mean": [0.485, 0.456, 0.406],
        "normalize_std": [0.229, 0.224, 0.225],
        "color_mode": "RGB"
    }
