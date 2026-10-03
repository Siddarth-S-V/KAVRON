from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ModelAsset:
    key: str
    filename: str
    url: str
    sha256: str | None = None
    kind: str = "onnx"
    optional: bool = True


MODEL_ASSETS: dict[str, ModelAsset] = {
    "face_detector": ModelAsset(
        "face_detector", "face_detection_yunet_2023mar.onnx",
        "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    ),
    "face_recognizer": ModelAsset(
        "face_recognizer", "face_recognition_sface_2021dec.onnx",
        "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
    ),
    "face_recognizer_int8": ModelAsset(
        "face_recognizer_int8", "face_recognition_sface_2021dec_int8bq.onnx",
        "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/face_recognition_sface/face_recognition_sface_2021dec_int8bq.onnx",
    ),
    "plate_detector": ModelAsset(
        "plate_detector", "license_plate_detection_lpd_yunet_2023mar.onnx",
        "https://github.com/opencv/opencv_zoo/raw/refs/heads/main/models/license_plate_detection_yunet/license_plate_detection_lpd_yunet_2023mar.onnx",
    ),
}


class ModelAssetManager:
    """Atomic downloader plus local-asset health checks.

    Local model files always win. Downloads are opt-in and never block API
    startup unless explicitly requested through the download endpoint/script.
    """
    def __init__(self, model_dir: str, timeout: int = 120) -> None:
        self.model_dir = Path(model_dir)
        self.timeout = timeout
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def path(self, key: str) -> Path:
        return self.model_dir / MODEL_ASSETS[key].filename

    def status(self) -> dict[str, dict]:
        result = {}
        for key, asset in MODEL_ASSETS.items():
            path = self.model_dir / asset.filename
            result[key] = {
                **asdict(asset),
                "path": str(path),
                "present": path.exists() and path.stat().st_size > 0,
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        return result

    def local_status(self) -> dict[str, dict]:
        result = {}
        for path in sorted(self.model_dir.glob("*")):
            if not path.is_file():
                continue
            result[path.name] = {"path": str(path), "size_bytes": path.stat().st_size}
        return result

    def ensure(self, key: str, force: bool = False) -> Path:
        if key not in MODEL_ASSETS:
            raise KeyError(f"Unknown model asset: {key}")
        asset = MODEL_ASSETS[key]
        destination = self.model_dir / asset.filename
        if destination.exists() and destination.stat().st_size > 0 and not force:
            self._verify(destination, asset)
            return destination

        fd, tmp_name = tempfile.mkstemp(prefix=f".{asset.filename}.", suffix=".part", dir=self.model_dir)
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            req = Request(asset.url, headers={"User-Agent": "KAVRON-Intelligence/3.0"})
            with urlopen(req, timeout=self.timeout) as response, tmp.open("wb") as out:
                shutil.copyfileobj(response, out, length=1024 * 1024)
            if tmp.stat().st_size == 0:
                raise RuntimeError(f"Downloaded empty model: {asset.url}")
            self._verify(tmp, asset)
            tmp.replace(destination)
            return destination
        finally:
            tmp.unlink(missing_ok=True)

    @staticmethod
    def _verify(path: Path, asset: ModelAsset) -> None:
        if not asset.sha256:
            return
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest().lower() != asset.sha256.lower():
            raise RuntimeError(f"Checksum mismatch for {asset.filename}")
