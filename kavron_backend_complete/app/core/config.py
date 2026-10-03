from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "KAVRON Intelligence API"
    version: str = "1.0.0"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    database_url: str = f"sqlite:///{ROOT_DIR / 'kavron.db'}"
    model_dir: str = str(ROOT_DIR / "models")
    demo_video: str = str(ROOT_DIR / "data" / "user_demo_01.mp4")
    device: str = "cpu"
    general_model: str = "yolo11n.pt"
    detector_candidates: str = "yolo11n.pt,yolo26n.pt,yolo26s.pt"
    person_model: str = "yolo11n_person.pt"
    pose_model: str = "yolo11n_pose.pt"
    specialist_model: str = "yolo11n1.pt"
    pose_alt_model: str = "yolo11n-pose.pt"
    ai_fps: float = 8.0
    stream_jpeg_fps: float = 12.0
    max_queue_size: int = 2
    inference_workers: int = 2
    scheduler_queue_size: int = 8
    pose_interval: int = 2
    tracker_max_age: float = 1.5
    tracker_max_distance: float = 120.0
    bbox_smoothing: float = 0.65
    pose_smoothing: float = 0.55
    max_cpu_threads: int = 0
    confidence: float = 0.35
    iou: float = 0.45
    max_cameras: int = 16
    enable_yolo: bool = True
    enable_deepsort: bool = True
    enable_person_specialist: bool = False
    stage3_enabled: bool = True
    auto_download_specialist_models: bool = False
    face_detector_filename: str = "face_detection_yunet_2023mar.onnx"
    plate_detector_filename: str = "license_plate_detection_lpd_yunet_2023mar.onnx"
    paddleocr_model_dir: str = str(ROOT_DIR / "models" / "paddleocr" / "en_PP-OCRv5_mobile_rec")
    specialist_workers: int = 2
    enable_rtmpose: bool = False
    face_interval: int = 4
    anpr_interval: int = 5
    enable_face_embedding: bool = False
    anpr_confidence: float = 0.45
    behavior_loiter_seconds: float = 12.0
    behavior_running_speed_px_s: float = 350.0
    jwt_secret: str = "change-this-secret-in-production"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
