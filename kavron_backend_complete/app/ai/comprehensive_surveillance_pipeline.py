"""
Optimized Multi-Task AI Pipeline:
1. High-Accuracy Person & Vehicle Detection & ByteTracking
2. Military / Army Forces & Civilian Vehicle Subtype Classification
3. Human-in-Vehicle / Rider Spatial Association (Occupant / Driver / Passenger / Motorcyclist)
4. License Plate Localization, Image Enhancement & Temporal Consensus ALPR (India, Pakistan, Military, International)
5. 17-Keypoint Smoothed Skeleton & Real-Time Pose Activity / Action Recognition
6. Facial Landmark Tracking (MediaPipe Face Mesh) & Re-ID Facial Recognition (MobileFaceNet)
7. Multi-threaded Camera Capture, Async Recording/Photo Saving, and Rich HUD Overlay
"""

import argparse
import glob
import math
import os
import queue
import re
import threading
import time
from collections import OrderedDict, deque
from datetime import datetime

import cv2
import numpy as np
import torch
from ultralytics import YOLO

# OCR dependency
try:
    import easyocr
    _HAS_EASYOCR = True
except ImportError:
    _HAS_EASYOCR = False

# CPU / GPU & OpenCV acceleration
_NUM_CORES = max(1, os.cpu_count() or 4)
torch.set_num_threads(_NUM_CORES)
cv2.setNumThreads(_NUM_CORES)
try:
    cv2.ocl.setUseOpenCL(True)
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOLO_POSE_WEIGHTS = os.path.join(BASE_DIR, "models", "yolo11n_pose.pt")
YOLO_DET_WEIGHTS = os.path.join(BASE_DIR, "models", "yolo11n.pt")
TRACKER_CFG = os.path.join(BASE_DIR, "models", "bytetrack.yaml")
FACE_LANDMARKER_MODEL = os.path.join(BASE_DIR, "models", "face_landmarker.task")
MOBILEFACENET_MODEL = os.path.join(BASE_DIR, "models", "mobilefacenet.onnx")
KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")

RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)
PHOTOS_DIR = os.path.join(RECORDINGS_DIR, "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

# COCO Base Vehicle Class IDs
COCO_VEHICLE_CLASSES = {
    1: "Bicycle",
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

# Regex for Indian, Pakistani, Military, and International License Plates
REGEX_INDIA = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$")
REGEX_INDIAN_MILITARY = re.compile(r"^[↑\^/\\]?[0-9]{2}[A-Z][0-9]{5,6}[A-Z]?$")
REGEX_PAKISTAN = re.compile(r"^[A-Z]{2,3}[- ]?[0-9]{2,4}[- ]?[0-9]{1,4}$")
REGEX_GENERAL_ALPR = re.compile(r"^[A-Z0-9]{4,12}$")


def _timestamp_str() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def clean_plate_text(text: str) -> str:
    """Removes noise and standardizes alphanumeric plate text."""
    # Convert common OCR character misidentifications if applicable
    raw = text.upper().strip()
    clean = re.sub(r"[^A-Z0-9↑\^/\\-]", "", raw)
    return clean


def classify_country_plate(text: str) -> tuple[str, str]:
    """
    Classifies clean plate text into:
    - IN: Indian Civilian
    - MIL: Indian / Armed Forces Defense Plate (Arrow prefix / military format)
    - PAK: Pakistani Standard
    - INTL: General Alphanumeric Plate
    - UNKNOWN
    """
    clean = clean_plate_text(text)
    clean_no_hyphen = clean.replace("-", "").replace(" ", "")

    if REGEX_INDIAN_MILITARY.match(clean_no_hyphen):
        # Format military plate nicely with arrow symbol
        formatted = clean_no_hyphen
        if not formatted.startswith("↑"):
            formatted = "↑ " + formatted.lstrip("^/\\")
        return formatted, "MIL"

    if REGEX_INDIA.match(clean_no_hyphen):
        return clean_no_hyphen, "IN"

    if REGEX_PAKISTAN.match(clean):
        return clean, "PAK"

    if REGEX_GENERAL_ALPR.match(clean_no_hyphen) and len(clean_no_hyphen) >= 5:
        return clean_no_hyphen, "INTL"

    return clean_no_hyphen if len(clean_no_hyphen) >= 4 else clean, "UNKNOWN"


# ==============================================================================
# MILITARY & TACTICAL VEHICLE HEURISTIC CLASSIFIER
# ==============================================================================
def inspect_military_vehicle(vehicle_crop, base_category: str) -> tuple[str, bool, float]:
    """
    Analyzes vehicle color distribution (Olive Drab, Camo Green, Desert Khaki, Matte Tactical)
    and geometry to classify military/army vehicles (Jeeps, Tactical Trucks, Armored/Troop Lorries).
    """
    if vehicle_crop is None or vehicle_crop.size == 0:
        return base_category, False, 0.0

    try:
        hsv = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2HSV)
        total_pixels = vehicle_crop.shape[0] * vehicle_crop.shape[1]
        if total_pixels < 100:
            return base_category, False, 0.0

        # Olive Drab & Army Tactical Green range
        mask_olive = cv2.inRange(hsv, np.array([32, 25, 20]), np.array([85, 200, 160]))
        # Desert Khaki / Tan Army Camo range
        mask_khaki = cv2.inRange(hsv, np.array([14, 25, 45]), np.array([30, 180, 210]))
        # Dark Matte / Camo Shadow range
        mask_matte_dark = cv2.inRange(hsv, np.array([0, 0, 15]), np.array([180, 55, 75]))

        combined_mask = cv2.bitwise_or(mask_olive, mask_khaki)
        combined_mask = cv2.bitwise_or(combined_mask, mask_matte_dark)

        military_pixels = cv2.countNonZero(combined_mask)
        military_ratio = float(military_pixels) / float(total_pixels)

        # Evaluate threshold
        if military_ratio > 0.28:
            if base_category in ["Truck", "Bus"]:
                specific_label = "Military Army Lorry" if base_category == "Truck" else "Military Troop Carrier"
                return specific_label, True, military_ratio
            elif base_category == "Car":
                return "Military Tactical Jeep/SUV", True, military_ratio
            elif base_category == "Motorcycle":
                return "Military Dispatch Bike", True, military_ratio

        # Map refined civilian vehicle names
        refined_civilian = {
            "Bicycle": "Bicycle / Cycle",
            "Car": "Car / SUV",
            "Bus": "Bus / Coach",
            "Truck": "Truck / Heavy Lorry",
            "Motorcycle": "Motorcycle / Bike"
        }.get(base_category, base_category)

        return refined_civilian, False, military_ratio

    except Exception:
        return base_category, False, 0.0


# ==============================================================================
# LICENSE PLATE LOCALIZATION & OCR (ALPR)
# ==============================================================================
class LicensePlateOCR:
    """High-accuracy License Plate Localizer & OCR with temporal voting per vehicle."""

    def __init__(self):
        self.enabled = _HAS_EASYOCR
        self.reader = None
        self.history_buffers: dict[int, deque] = {}

        if self.enabled:
            use_gpu = torch.cuda.is_available()
            try:
                # English reader handles standard alphanumeric + defense plate codes
                self.reader = easyocr.Reader(["en"], gpu=use_gpu, verbose=False)
            except Exception as e:
                print(f"[WARN] Could not initialize EasyOCR: {e}")
                self.enabled = False
        else:
            print("[WARN] EasyOCR not installed. Run 'pip install easyocr' for plate recognition.")

    def _localize_plate_candidates(self, vehicle_crop) -> list[np.ndarray]:
        """Extracts candidate license plate patches using morphological and edge transforms."""
        candidates = []
        vh, vw = vehicle_crop.shape[:2]
        if vh < 30 or vw < 40:
            return [vehicle_crop]

        # License plates are predominantly in the bottom 45% of vehicles (front/rear bumpers)
        bottom_region = vehicle_crop[int(vh * 0.48):vh, 0:vw]
        if bottom_region.size > 0:
            candidates.append(bottom_region)

        # Full vehicle crop fallback
        candidates.append(vehicle_crop)

        # Morphological plate edge contour search on bottom region
        try:
            gray = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)
            # Blackhat transform reveals bright letters/plates on dark borders or vice versa
            rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))
            blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rect_kernel)

            # Sobel horizontal gradients
            grad_x = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
            grad_x = np.absolute(grad_x)
            min_val, max_val = np.min(grad_x), np.max(grad_x)
            if max_val > min_val:
                grad_x = (255 * ((grad_x - min_val) / (max_val - min_val))).astype("uint8")
            else:
                grad_x = grad_x.astype("uint8")

            # Blur and threshold
            grad_x = cv2.GaussianBlur(grad_x, (5, 5), 0)
            _, thresh = cv2.threshold(grad_x, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

            # Connect plate blocks
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, rect_kernel)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / float(h)
                # Plate aspect ratio is typically between 1.8 and 5.8
                if 1.8 <= aspect_ratio <= 5.8 and w > 35 and h > 12:
                    pad_x = int(w * 0.08)
                    pad_y = int(h * 0.08)
                    x1 = max(0, x - pad_x)
                    y1 = max(0, y - pad_y)
                    x2 = min(bottom_region.shape[1], x + w + pad_x)
                    y2 = min(bottom_region.shape[0], y + h + pad_y)
                    candidate = bottom_region[y1:y2, x1:x2]
                    if candidate.size > 0:
                        candidates.insert(0, candidate)
        except Exception:
            pass

        return candidates

    def _preprocess_plate_for_ocr(self, patch: np.ndarray) -> np.ndarray:
        """Applies CLAHE contrast enhancement, resizing, and sharpening to maximize OCR accuracy."""
        if patch.size == 0:
            return patch

        ph, pw = patch.shape[:2]
        # Resize to optimal OCR character height (120-160px)
        scale = max(1.0, 140.0 / max(ph, 1))
        target_w, target_h = int(pw * scale), int(ph * scale)
        resized = cv2.resize(patch, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Bilateral filter removes noise while keeping character edges sharp
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
        return denoised

    def read_plate(self, vehicle_crop: np.ndarray, track_id: int = -1) -> tuple[str, str, float]:
        """Runs candidate extraction, OCR recognition, regex classification, and rolling consensus."""
        if not self.enabled or self.reader is None or vehicle_crop is None or vehicle_crop.size == 0:
            return "", "UNKNOWN", 0.0

        best_plate, best_country, best_conf = "", "UNKNOWN", 0.0
        candidates = self._localize_plate_candidates(vehicle_crop)

        # Test up to top 3 candidate regions
        for cand in candidates[:3]:
            preprocessed = self._preprocess_plate_for_ocr(cand)
            try:
                ocr_results = self.reader.readtext(
                    preprocessed,
                    detail=1,
                    paragraph=False,
                    allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789↑^-/ "
                )
                if not ocr_results:
                    continue

                # Combine text chunks if detected in lines
                for bbox, text, conf in ocr_results:
                    if conf < 0.25:
                        continue
                    plate_str, country = classify_country_plate(text)
                    if len(plate_str) >= 4 and conf > best_conf:
                        best_plate = plate_str
                        best_country = country
                        best_conf = float(conf)

            except Exception:
                continue

            if best_conf > 0.65:
                break

        # Temporal majority voting buffer for persistent track ID
        if track_id != -1 and best_plate:
            if track_id not in self.history_buffers:
                self.history_buffers[track_id] = deque(maxlen=9)
            self.history_buffers[track_id].append((best_plate, best_country, best_conf))

            # Vote consensus
            vote_counts: dict[str, int] = {}
            country_map: dict[str, str] = {}
            conf_map: dict[str, float] = {}

            for p_text, p_cntry, p_c in self.history_buffers[track_id]:
                vote_counts[p_text] = vote_counts.get(p_text, 0) + 1
                country_map[p_text] = p_cntry
                conf_map[p_text] = max(conf_map.get(p_text, 0.0), p_c)

            winner_plate = max(vote_counts, key=lambda k: (vote_counts[k], conf_map.get(k, 0.0)))
            return winner_plate, country_map.get(winner_plate, best_country), conf_map.get(winner_plate, best_conf)

        return best_plate, best_country, best_conf

    def prune_buffers(self, active_track_ids: set):
        stale_ids = [tid for tid in self.history_buffers if tid not in active_track_ids]
        for tid in stale_ids:
            del self.history_buffers[tid]


# ==============================================================================
# HUMAN POSE ACTIVITY & ACTION RECOGNITION ENGINE
# ==============================================================================
# COCO 17 Keypoints:
# 0: Nose, 1: L_Eye, 2: R_Eye, 3: L_Ear, 4: R_Ear,
# 5: L_Shoulder, 6: R_Shoulder, 7: L_Elbow, 8: R_Elbow, 9: L_Wrist, 10: R_Wrist,
# 11: L_Hip, 12: R_Hip, 13: L_Knee, 14: R_Knee, 15: L_Ankle, 16: R_Ankle

def classify_human_action(keypoints_xy: list, keypoints_conf: list, in_vehicle_type: str = None) -> tuple[str, str]:
    """
    Kinematic geometric rule-based action classifier:
    - Driving / Steering
    - Riding Bike / Cycling
    - Seated Passenger
    - Calling / Phone to Ear
    - Hands Raised / Signalling / Surrender
    - Walking / Running
    - Standing / Idle
    - Bending / Crouching
    - Fallen / Lying Down
    """
    if not keypoints_xy or len(keypoints_xy) < 17:
        if in_vehicle_type:
            return ("Driving" if "Motorcycle" not in in_vehicle_type else "Riding"), "Normal"
        return "Standing / Active", "Normal"

    def get_kpt(idx):
        conf = keypoints_conf[idx] if keypoints_conf and idx < len(keypoints_conf) else 1.0
        return np.array(keypoints_xy[idx]), conf

    nose, c_nose = get_kpt(0)
    l_ear, c_lear = get_kpt(3)
    r_ear, c_rear = get_kpt(4)
    l_sh, c_lsh = get_kpt(5)
    r_sh, c_rsh = get_kpt(6)
    l_el, c_lel = get_kpt(7)
    r_el, c_rel = get_kpt(8)
    l_wr, c_lwr = get_kpt(9)
    r_wr, c_rwr = get_kpt(10)
    l_hip, c_lhip = get_kpt(11)
    r_hip, c_rhip = get_kpt(12)
    l_knee, c_lknee = get_kpt(13)
    r_knee, c_rknee = get_kpt(14)
    l_ank, c_lank = get_kpt(15)
    r_ank, c_rank = get_kpt(16)

    # Midpoints and scale reference
    mid_shoulder = (l_sh + r_sh) / 2.0
    mid_hip = (l_hip + r_hip) / 2.0
    torso_height = max(10.0, np.linalg.norm(mid_shoulder - mid_hip))

    # 1. Check Fallen / Lying Down (Torso horizontal)
    if c_lsh > 0.3 and c_rsh > 0.3 and c_lhip > 0.3 and c_rhip > 0.3:
        torso_dy = abs(mid_shoulder[1] - mid_hip[1])
        torso_dx = abs(mid_shoulder[0] - mid_hip[0])
        if torso_dx > torso_dy * 1.6 and torso_dy < 40:
            return "Fallen / Lying Down", "Alert"

    # 2. Check Hands Raised / Surrender / Waving (Wrists well above nose/eyes)
    if (c_lwr > 0.4 and l_wr[1] < nose[1] - 20) and (c_rwr > 0.4 and r_wr[1] < nose[1] - 20):
        return "Hands Raised (Surrender / Alert)", "Warning"
    if (c_lwr > 0.4 and l_wr[1] < nose[1] - 30) or (c_rwr > 0.4 and r_wr[1] < nose[1] - 30):
        return "Waving / Signalling", "Normal"

    # 3. Check Phone to Ear / Calling
    phone_threshold = torso_height * 0.32
    if c_lear > 0.3 and c_lwr > 0.4 and np.linalg.norm(l_wr - l_ear) < phone_threshold:
        return "Calling / Phone to Ear", "Normal"
    if c_rear > 0.3 and c_rwr > 0.4 and np.linalg.norm(r_wr - r_ear) < phone_threshold:
        return "Calling / Phone to Ear", "Normal"

    # 4. Vehicle Specific Postures
    if in_vehicle_type:
        if "Motorcycle" in in_vehicle_type or "Bike" in in_vehicle_type:
            return "Riding Motorcycle/Bike", "Active"
        elif "Military" in in_vehicle_type:
            # Check driving steering hand posture
            if c_lwr > 0.3 and c_rwr > 0.3 and l_wr[1] < mid_hip[1] and r_wr[1] < mid_hip[1]:
                return "Military Vehicle Driver / Steering", "Tactical"
            return "Military Crew / Occupant", "Tactical"
        elif "Truck" in in_vehicle_type or "Lorry" in in_vehicle_type:
            return "Truck/Lorry Driver", "Normal"
        elif "Car" in in_vehicle_type:
            if c_lwr > 0.3 and c_rwr > 0.3 and (l_wr[1] < mid_hip[1] and r_wr[1] < mid_hip[1]):
                return "Driving / Steering Wheel", "Normal"
            return "In-Car Passenger", "Normal"
        elif "Bus" in in_vehicle_type:
            return "Bus Driver / Passenger", "Normal"

    # 5. Check Bending / Crouching / Squatting
    if c_lknee > 0.3 and c_lhip > 0.3 and c_lank > 0.3:
        knee_flex = abs(l_hip[1] - l_knee[1])
        if knee_flex < torso_height * 0.55:
            return "Crouching / Bending", "Normal"

    # 6. Check Walking vs Running vs Standing
    if c_lank > 0.3 and c_rank > 0.3:
        stride_dist = np.linalg.norm(l_ank - r_ank)
        if stride_dist > torso_height * 1.25:
            return "Running / High Stride", "Active"
        elif stride_dist > torso_height * 0.65:
            return "Walking / Moving", "Normal"

    # 7. Check Sitting posture on chair/bench
    if c_lhip > 0.3 and c_lknee > 0.3:
        if abs(l_hip[1] - l_knee[1]) < torso_height * 0.45:
            return "Sitting / Resting", "Normal"

    return "Standing / Idle", "Normal"


# ==============================================================================
# SPATIAL VEHICLE-HUMAN ASSOCIATION ENGINE
# ==============================================================================
def associate_humans_with_vehicles(persons: list, vehicles: list) -> None:
    """
    Computes spatial containment and intersection-over-person to detect
    occupants, drivers, passengers, and motorcyclists inside/on vehicles.
    """
    for person in persons:
        px1, py1, px2, py2 = person["box"]
        pw, ph = px2 - px1, py2 - py1
        p_area = max(1, pw * ph)
        p_center_x = (px1 + px2) / 2.0
        p_center_y = (py1 + py2) / 2.0
        p_bottom_y = py2

        best_match_veh = None
        best_overlap_ratio = 0.0

        for veh in vehicles:
            vx1, vy1, vx2, vy2 = veh["box"]

            # Calculate intersection
            ix1 = max(px1, vx1)
            iy1 = max(py1, vy1)
            ix2 = min(px2, vx2)
            iy2 = min(py2, vy2)

            if ix2 > ix1 and iy2 > iy1:
                intersection_area = (ix2 - ix1) * (iy2 - iy1)
                overlap_ratio = float(intersection_area) / float(p_area)

                # Or check if human center/lower body is within vehicle bounding box
                center_inside = (vx1 <= p_center_x <= vx2) and (vy1 <= p_bottom_y <= vy2 + int((vy2 - vy1) * 0.15))

                if (overlap_ratio > 0.30 or center_inside) and overlap_ratio > best_overlap_ratio:
                    best_overlap_ratio = overlap_ratio
                    best_match_veh = veh

        if best_match_veh is not None:
            veh_id = best_match_veh["track_id"]
            veh_cat = best_match_veh["category"]
            person["in_vehicle_id"] = veh_id
            person["in_vehicle_type"] = veh_cat

            # Classify specific role
            if "Motorcycle" in veh_cat or "Bike" in veh_cat:
                person["role"] = f"Rider on {veh_cat} #{veh_id}"
            elif "Military" in veh_cat:
                person["role"] = f"Personnel in {veh_cat} #{veh_id}"
            elif "Car" in veh_cat:
                # Approximate driver side
                vx1, _, vx2, _ = best_match_veh["box"]
                side = "Driver (Right/Front)" if p_center_x > (vx1 + vx2) / 2.0 else "Driver/Passenger (Left/Front)"
                person["role"] = f"{side} in Car #{veh_id}"
            elif "Bus" in veh_cat:
                person["role"] = f"Occupant in Bus #{veh_id}"
            elif "Truck" in veh_cat or "Lorry" in veh_cat:
                person["role"] = f"Crew in Truck #{veh_id}"
            else:
                person["role"] = f"Inside {veh_cat} #{veh_id}"

            # Link to vehicle occupant list
            best_match_veh.setdefault("occupants", []).append(person["track_id"])
        else:
            person["in_vehicle_id"] = None
            person["in_vehicle_type"] = None
            person["role"] = "Pedestrian / On Foot"


# ==============================================================================
# KEYPOINT SMOOTHING & DRAWING
# ==============================================================================
SKELETON_EDGES = [
    (15, 13), (13, 11), (16, 14), (14, 12), (11, 12),
    (5, 11), (6, 12), (5, 6),
    (5, 7), (7, 9), (6, 8), (8, 10),
    (0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6),
]
_LIMB_COLORS = {
    "legs":  (0, 160, 255),
    "torso": (0, 240, 180),
    "arms":  (255, 190, 0),
    "head":  (220, 90, 255),
}
_EDGE_GROUPS = (
    ["legs"]  * 5 +
    ["torso"] * 3 +
    ["arms"]  * 4 +
    ["head"]  * 6
)
_UPPER_BODY_IDX = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10}


def draw_skeleton(frame: np.ndarray, keypoints_xy: list, keypoints_conf: list = None) -> np.ndarray:
    if not keypoints_xy:
        return frame

    def visible(i):
        if keypoints_conf is None:
            return True
        return keypoints_conf[i] >= 0.30

    for edge_idx, (a, b) in enumerate(SKELETON_EDGES):
        if a >= len(keypoints_xy) or b >= len(keypoints_xy):
            continue
        if not (visible(a) and visible(b)):
            continue
        xa, ya = keypoints_xy[a]
        xb, yb = keypoints_xy[b]
        if (xa == 0 and ya == 0) or (xb == 0 and yb == 0):
            continue
        group = _EDGE_GROUPS[edge_idx]
        color = _LIMB_COLORS[group]
        cv2.line(frame, (int(xa), int(ya)), (int(xb), int(yb)), color, 2, cv2.LINE_AA)

    for i, (x, y) in enumerate(keypoints_xy):
        if (x == 0 and y == 0) or not visible(i):
            continue
        color = (255, 170, 0) if i in _UPPER_BODY_IDX else (0, 160, 255)
        cv2.circle(frame, (int(x), int(y)), 4, color, -1, cv2.LINE_AA)
        cv2.circle(frame, (int(x), int(y)), 5, (20, 20, 20), 1, cv2.LINE_AA)

    return frame


class KeypointSmoother:
    def __init__(self, alpha: float = 0.75):
        self.alpha = alpha
        self._history: dict[int, np.ndarray] = {}

    def smooth(self, track_id: int, keypoints_xy: list) -> list:
        if not keypoints_xy:
            return keypoints_xy
        kpts = np.array(keypoints_xy, dtype=np.float32)
        if track_id not in self._history:
            self._history[track_id] = kpts.copy()
            return keypoints_xy

        prev = self._history[track_id]
        mask = (kpts[:, 0] != 0) | (kpts[:, 1] != 0)
        smoothed = prev.copy()
        smoothed[mask] = self.alpha * kpts[mask] + (1.0 - self.alpha) * prev[mask]
        self._history[track_id] = smoothed
        return smoothed.tolist()

    def prune(self, active_ids: set):
        stale = [tid for tid in self._history if tid not in active_ids]
        for tid in stale:
            del self._history[tid]


# ==============================================================================
# FACIAL TRACKING & RE-ID IDENTIFIER
# ==============================================================================
class FaceMeshTracker:
    def __init__(self, max_faces=8, min_detection_conf=0.60, min_tracking_conf=0.60,
                 iou_thresh=0.35, max_missed=25):
        self.available = False
        self.boxes = OrderedDict()
        self.landmarks = OrderedDict()
        self.missed = OrderedDict()
        self.next_id = 1
        self.iou_thresh = iou_thresh
        self.max_missed = max_missed
        self._last_timestamp_ms = -1

        if os.path.isfile(FACE_LANDMARKER_MODEL):
            try:
                import mediapipe as mp
                from mediapipe.tasks import python as mp_python
                from mediapipe.tasks.python import vision as mp_vision

                self._mp = mp
                base_options = mp_python.BaseOptions(model_asset_path=FACE_LANDMARKER_MODEL)
                options = mp_vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    running_mode=mp_vision.RunningMode.VIDEO,
                    num_faces=max_faces,
                    min_face_detection_confidence=min_detection_conf,
                    min_face_presence_confidence=min_detection_conf,
                    min_tracking_confidence=min_tracking_conf,
                )
                self.landmarker = mp_vision.FaceLandmarker.create_from_options(options)
                self.available = True
            except Exception as e:
                print(f"[WARN] MediaPipe Face Landmarker could not load: {e}")

    def _next_timestamp_ms(self):
        ts = int(time.time() * 1000)
        if ts <= self._last_timestamp_ms:
            ts = self._last_timestamp_ms + 1
        self._last_timestamp_ms = ts
        return ts

    def process(self, frame: np.ndarray) -> dict:
        if not self.available:
            return {}

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self.landmarker.detect_for_video(mp_image, self._next_timestamp_ms())

        detections = []
        if result.face_landmarks:
            for face_landmarks in result.face_landmarks:
                xs = [lm.x * w for lm in face_landmarks]
                ys = [lm.y * h for lm in face_landmarks]
                x1, x2 = max(0, int(min(xs))), min(w, int(max(xs)))
                y1, y2 = max(0, int(min(ys))), min(h, int(max(ys)))
                if (x2 - x1) < 20 or (y2 - y1) < 20:
                    continue
                box = (x1, y1, x2 - x1, y2 - y1)
                points = [(int(px), int(py)) for px, py in zip(xs, ys)]
                detections.append((box, points))

        return self._update_tracks(detections)

    @staticmethod
    def _iou(box_a, box_b):
        ax1, ay1, aw, ah = box_a
        bx1, by1, bw, bh = box_b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax1 + aw, bx1 + bw), min(ay1 + ah, by1 + bh)
        iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
        inter = iw * ih
        union = (aw * ah) + (bw * bh) - inter
        return inter / union if union > 0 else 0.0

    def _update_tracks(self, detections):
        if not detections:
            for oid in list(self.missed.keys()):
                self.missed[oid] += 1
                if self.missed[oid] > self.max_missed:
                    self._deregister(oid)
            return {oid: {"box": self.boxes[oid], "landmarks": self.landmarks[oid]} for oid in self.boxes}

        if not self.boxes:
            for box, pts in detections:
                self._register(box, pts)
        else:
            track_ids = list(self.boxes.keys())
            track_boxes = list(self.boxes.values())

            S = np.zeros((len(track_boxes), len(detections)))
            for i, tb in enumerate(track_boxes):
                for j, (db, _) in enumerate(detections):
                    S[i, j] = self._iou(tb, db)

            used_rows, used_cols = set(), set()
            flat_idx = np.dstack(np.unravel_index(np.argsort(-S, axis=None), S.shape))[0]
            for row, col in flat_idx:
                row, col = int(row), int(col)
                if row in used_rows or col in used_cols or S[row, col] < self.iou_thresh:
                    continue
                oid = track_ids[row]
                self.boxes[oid], self.landmarks[oid] = detections[col]
                self.missed[oid] = 0
                used_rows.add(row)
                used_cols.add(col)

            for row in set(range(len(track_boxes))) - used_rows:
                oid = track_ids[row]
                self.missed[oid] += 1
                if self.missed[oid] > self.max_missed:
                    self._deregister(oid)

            for col in set(range(len(detections))) - used_cols:
                self._register(*detections[col])

        return {oid: {"box": self.boxes[oid], "landmarks": self.landmarks[oid]} for oid in self.boxes}

    def _register(self, box, pts):
        self.boxes[self.next_id] = box
        self.landmarks[self.next_id] = pts
        self.missed[self.next_id] = 0
        self.next_id += 1

    def _deregister(self, oid):
        del self.boxes[oid]
        del self.landmarks[oid]
        del self.missed[oid]

    _CONTOUR_IDX = list(range(0, 478, 8))

    def draw(self, frame: np.ndarray, tracked_faces: dict, draw_mesh: bool = True) -> np.ndarray:
        for face_id, data in tracked_faces.items():
            x, y, w, h = data["box"]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 210), 2)
            label = data.get("label") or f"Face #{face_id}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            cv2.rectangle(frame, (x, max(0, y - th - 6)), (x + tw + 4, y), (255, 0, 210), -1)
            cv2.putText(frame, label, (x + 2, max(0, y - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

            if draw_mesh and "landmarks" in data:
                pts = data["landmarks"]
                for idx in self._CONTOUR_IDX:
                    if idx < len(pts):
                        cv2.circle(frame, pts[idx], 1, (0, 255, 255), -1)
        return frame


class MobileFaceNetIdentifier:
    INPUT_SIZE = (112, 112)

    def __init__(self, sim_thresh: float = 0.58):
        self.available = os.path.isfile(MOBILEFACENET_MODEL) and os.path.getsize(MOBILEFACENET_MODEL) > 500_000
        self.sim_thresh = sim_thresh
        self.known_embeddings: dict[str, np.ndarray] = {}
        self._vote_buffers: dict[int, deque] = {}
        self._cache: dict[int, tuple[str | None, float, int]] = {}

        if self.available:
            try:
                self.net = cv2.dnn.readNetFromONNX(MOBILEFACENET_MODEL)
                self._enroll_known_faces()
            except Exception as e:
                print(f"[WARN] MobileFaceNet ONNX could not load: {e}")
                self.available = False

    def _embed(self, face_bgr: np.ndarray) -> np.ndarray:
        face = cv2.resize(face_bgr, self.INPUT_SIZE)
        blob = cv2.dnn.blobFromImage(face, 1.0 / 128.0, self.INPUT_SIZE,
                                     (127.5, 127.5, 127.5), swapRB=True)
        self.net.setInput(blob)
        out = self.net.forward().flatten().astype(np.float32)
        norm = np.linalg.norm(out)
        return out / norm if norm > 1e-8 else out

    def _enroll_known_faces(self):
        if not os.path.isdir(KNOWN_FACES_DIR):
            return

        for person_dir in sorted(glob.glob(os.path.join(KNOWN_FACES_DIR, "*"))):
            if not os.path.isdir(person_dir):
                continue
            name = os.path.basename(person_dir)
            embeds = []
            for img_path in glob.glob(os.path.join(person_dir, "*.*")):
                img = cv2.imread(img_path)
                if img is None:
                    continue
                try:
                    embeds.append(self._embed(img))
                except Exception:
                    continue
            if embeds:
                avg = np.mean(embeds, axis=0).astype(np.float32)
                norm = np.linalg.norm(avg)
                self.known_embeddings[name] = avg / norm if norm > 1e-8 else avg

    def identify(self, face_id: int, face_crop: np.ndarray, frame_idx: int = 0) -> tuple[str | None, float]:
        if not self.available or not self.known_embeddings or face_crop is None or face_crop.size == 0:
            return None, 0.0

        if face_id in self._cache:
            name, sim, last_frame = self._cache[face_id]
            if (frame_idx - last_frame) < 4:
                return name, sim

        try:
            emb = self._embed(face_crop)
        except Exception:
            return None, 0.0

        best_name, best_sim = None, 0.0
        for name, known_emb in self.known_embeddings.items():
            sim = float(np.dot(emb, known_emb))
            if sim > best_sim:
                best_name, best_sim = name, sim

        if face_id not in self._vote_buffers:
            self._vote_buffers[face_id] = deque(maxlen=7)

        recognized = best_name if best_sim >= self.sim_thresh else None
        self._vote_buffers[face_id].append((recognized, best_sim))

        counts: dict[str | None, int] = {}
        sims: dict[str | None, float] = {}
        for r_name, r_sim in self._vote_buffers[face_id]:
            counts[r_name] = counts.get(r_name, 0) + 1
            sims[r_name] = max(sims.get(r_name, 0.0), r_sim)

        winner = max(counts, key=lambda k: (counts[k], sims.get(k, 0.0)))
        res_name = winner if winner is not None else None
        res_sim = sims.get(winner, best_sim)
        self._cache[face_id] = (res_name, res_sim, frame_idx)

        return res_name, res_sim

    def prune_buffers(self, active_face_ids: set):
        stale = [fid for fid in self._vote_buffers if fid not in active_face_ids]
        for fid in stale:
            del self._vote_buffers[fid]
            self._cache.pop(fid, None)


# ==============================================================================
# THREADED CAMERA & ASYNC SAVER
# ==============================================================================
class ThreadedCamera:
    """Threaded camera capture to maximize FPS without frame queue lag."""

    def __init__(self, src=0, target_fps=60, width=1280, height=720):
        self.src = src
        self.is_webcam = str(src).isdigit()

        if self.is_webcam:
            cam_idx = int(src)
            if os.name == "nt":
                self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(cam_idx)

            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            self.cap.set(cv2.CAP_PROP_FPS, target_fps)
            if width and height:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            self.cap = cv2.VideoCapture(src)

        self.stopped = False
        self.lock = threading.Lock()
        self.ret, self.frame = self.cap.read()

        if self.ret and self.frame is not None:
            self.width = self.frame.shape[1]
            self.height = self.frame.shape[0]
        else:
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def _update_loop(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if not ret:
                self.stopped = True
                break
            with self.lock:
                self.ret = ret
                self.frame = frame

    def read(self):
        with self.lock:
            if self.frame is None:
                return self.ret, None
            return self.ret, self.frame.copy()

    def isOpened(self):
        return self.cap.isOpened() and not (self.stopped and self.frame is None)

    def get(self, propId):
        return self.cap.get(propId)

    def release(self):
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join(timeout=0.5)
        self.cap.release()


class AsyncPhotoSaver:
    """Non-blocking background thread saving high-resolution event snapshots."""

    def __init__(self, photos_dir=PHOTOS_DIR, cooldown=3.0):
        self.photos_dir = photos_dir
        self.cooldown = cooldown
        self.queue = queue.Queue(maxsize=50)
        self.last_saved: dict[str, float] = {}
        self.saved_count = 0
        self.stopped = False
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def request_save(self, frame: np.ndarray, box: tuple, label: str, track_id: int = -1):
        key = f"{label}_{track_id}"
        now = time.time()
        if track_id != -1 and key in self.last_saved and (now - self.last_saved[key]) < self.cooldown:
            return False
        self.last_saved[key] = now

        x1, y1, x2, y2 = box
        crop = frame[y1:y2, x1:x2].copy()
        full = frame.copy()
        try:
            self.queue.put_nowait((crop, full, label, track_id, _timestamp_str()))
            return True
        except queue.Full:
            return False

    def _worker_loop(self):
        while not self.stopped:
            try:
                item = self.queue.get(timeout=0.2)
            except queue.Empty:
                continue
            crop, full, label, track_id, ts = item
            try:
                clean_label = re.sub(r"[^A-Za-z0-9_-]", "_", label)
                if crop.size > 0:
                    crop_path = os.path.join(self.photos_dir, f"{clean_label}_ID{track_id}_{ts}_crop.jpg")
                    cv2.imwrite(crop_path, crop)
                full_path = os.path.join(self.photos_dir, f"{clean_label}_ID{track_id}_{ts}_full.jpg")
                cv2.imwrite(full_path, full)
                self.saved_count += 1
            except Exception:
                pass
            finally:
                self.queue.task_done()

    def stop(self):
        self.stopped = True


# ==============================================================================
# ACCURACY STATS TRACKER
# ==============================================================================
class AccuracyStats:
    def __init__(self, window=30):
        self.total_frames = 0
        self.total_persons = 0
        self.total_vehicles = 0
        self.total_plates = 0
        self.fps_buffer = deque(maxlen=window)
        self.session_start = time.time()

    def update(self, persons: list, vehicles: list, fps: float):
        self.total_frames += 1
        self.total_persons += len(persons)
        self.total_vehicles += len(vehicles)
        for v in vehicles:
            if v.get("plate"):
                self.total_plates += 1
        self.fps_buffer.append(fps)

    @property
    def avg_fps(self):
        return float(np.mean(self.fps_buffer)) if self.fps_buffer else 0.0


# ==============================================================================
# MAIN COMPREHENSIVE AI PIPELINE
# ==============================================================================
class ComprehensiveAIPipeline:
    """Integrated Real-Time AI Pipeline with Pose, Vehicles, Military Recognition, ALPR, and Face Re-ID."""

    def __init__(self, conf_thresh: float = 0.30, imgsz: int = 640, device: str = None):
        self.device = device or ("0" if torch.cuda.is_available() else "cpu")
        self.conf_thresh = conf_thresh
        self.imgsz = imgsz
        self.frame_count = 0
        self.draw_mesh = True
        self.show_hud = True

        print(f"[INFO] Initializing YOLO Models on device: {self.device}")
        # Human Pose & Detection
        self.pose_detector = YOLO(YOLO_POSE_WEIGHTS if os.path.isfile(YOLO_POSE_WEIGHTS) else "yolo11n-pose.pt")
        # Vehicle & Object Detection
        self.vehicle_detector = YOLO(YOLO_DET_WEIGHTS if os.path.isfile(YOLO_DET_WEIGHTS) else "yolo11n.pt")

        # Subsystems
        self.face_tracker = FaceMeshTracker()
        self.identifier = MobileFaceNetIdentifier()
        self.plate_ocr = LicensePlateOCR()
        self.kpt_smoother = KeypointSmoother(alpha=0.75)

    def process_frame(self, frame: np.ndarray):
        self.frame_count += 1
        h, w = frame.shape[:2]

        # ---------------------------------------------------------
        # 1. VEHICLE DETECTION, TRACKING & CLASSIFICATION
        # ---------------------------------------------------------
        veh_results = self.vehicle_detector.track(
            frame,
            classes=list(COCO_VEHICLE_CLASSES.keys()),
            conf=self.conf_thresh,
            tracker=TRACKER_CFG,
            persist=True,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False
        )

        vehicles = []
        active_veh_ids = set()

        if veh_results and veh_results[0].boxes is not None and len(veh_results[0].boxes) > 0:
            for box in veh_results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                track_id = int(box.id[0]) if box.id is not None else -1

                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 <= x1 or y2 <= y1:
                    continue

                if track_id != -1:
                    active_veh_ids.add(track_id)

                base_category = COCO_VEHICLE_CLASSES.get(cls_id, "Vehicle")
                v_crop = frame[y1:y2, x1:x2]

                # Inspect for Military / Army Forces heuristic
                refined_category, is_military, mil_score = inspect_military_vehicle(v_crop, base_category)

                # Plate detection and multi-frame voting
                plate_str, country, p_conf = self.plate_ocr.read_plate(v_crop, track_id=track_id)

                # If plate matches military format, upgrade tag
                if country == "MIL":
                    is_military = True
                    if "Military" not in refined_category:
                        refined_category = f"Military {refined_category}"

                vehicles.append({
                    "track_id": track_id,
                    "box": (x1, y1, x2, y2),
                    "conf": conf,
                    "category": refined_category,
                    "is_military": is_military,
                    "military_score": mil_score,
                    "plate": plate_str,
                    "country": country,
                    "plate_conf": p_conf,
                    "occupants": []
                })

        self.plate_ocr.prune_buffers(active_veh_ids)

        # ---------------------------------------------------------
        # 2. HUMAN POSE SKELETON & TRACKING
        # ---------------------------------------------------------
        pose_results = self.pose_detector.track(
            frame,
            classes=[0],
            conf=self.conf_thresh,
            tracker=TRACKER_CFG,
            persist=True,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
            iou=0.45
        )

        persons = []
        active_person_ids = set()

        if pose_results and pose_results[0].boxes is not None and len(pose_results[0].boxes) > 0:
            boxes = pose_results[0].boxes
            kpts_xy_all = pose_results[0].keypoints.xy if pose_results[0].keypoints is not None else None
            kpts_conf_all = pose_results[0].keypoints.conf if pose_results[0].keypoints is not None else None

            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])
                track_id = int(box.id[0]) if box.id is not None else -1

                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 <= x1 or y2 <= y1:
                    continue

                if track_id != -1:
                    active_person_ids.add(track_id)

                keypoints_xy = kpts_xy_all[i].tolist() if kpts_xy_all is not None else []
                keypoints_conf = kpts_conf_all[i].tolist() if kpts_conf_all is not None else None

                if keypoints_xy and track_id != -1:
                    keypoints_xy = self.kpt_smoother.smooth(track_id, keypoints_xy)

                persons.append({
                    "track_id": track_id,
                    "box": (x1, y1, x2, y2),
                    "conf": conf,
                    "keypoints": keypoints_xy,
                    "keypoints_conf": keypoints_conf,
                    "in_vehicle_id": None,
                    "in_vehicle_type": None,
                    "role": "Pedestrian",
                    "action": "Standing",
                    "action_status": "Normal",
                    "face_name": None,
                    "face_sim": 0.0
                })

        self.kpt_smoother.prune(active_person_ids)

        # ---------------------------------------------------------
        # 3. SPATIAL ASSOCIATION: HUMANS IN VEHICLES & POSE ACTIONS
        # ---------------------------------------------------------
        associate_humans_with_vehicles(persons, vehicles)

        for person in persons:
            action, status = classify_human_action(
                person["keypoints"],
                person.get("keypoints_conf"),
                in_vehicle_type=person["in_vehicle_type"]
            )
            person["action"] = action
            person["action_status"] = status

        # ---------------------------------------------------------
        # 4. FACIAL TRACKING & RE-ID IDENTIFICATION
        # ---------------------------------------------------------
        tracked_faces = self.face_tracker.process(frame)
        active_face_ids = set(tracked_faces.keys())

        for face_id, face_data in tracked_faces.items():
            fx, fy, fw, fh = face_data["box"]
            face_crop = frame[fy:fy + fh, fx:fx + fw]
            name, sim = self.identifier.identify(face_id, face_crop, frame_idx=self.frame_count)
            face_data["name"] = name
            face_data["sim"] = sim
            face_data["label"] = f"{name} ({sim:.2f})" if name else f"Face #{face_id}"

            # Link face to corresponding person
            fc_x, fc_y = fx + fw / 2.0, fy + fh / 2.0
            for person in persons:
                px1, py1, px2, py2 = person["box"]
                if px1 <= fc_x <= px2 and py1 <= fc_y <= py2:
                    person["face_name"] = name
                    person["face_sim"] = sim
                    break

        self.identifier.prune_buffers(active_face_ids)

        return persons, vehicles, tracked_faces

    def render_overlay(self, frame: np.ndarray, persons: list, vehicles: list, tracked_faces: dict,
                       stats: AccuracyStats = None, fps: float = 0.0) -> np.ndarray:
        annotated = frame.copy()
        h, w = frame.shape[:2]

        # ---------------------------------------------------------
        # 1. RENDER VEHICLES & LICENSE PLATES
        # ---------------------------------------------------------
        for veh in vehicles:
            x1, y1, x2, y2 = veh["box"]
            track_id = veh["track_id"]
            cat = veh["category"]
            is_mil = veh.get("is_military", False)
            plate = veh.get("plate", "")
            country = veh.get("country", "UNKNOWN")
            occupants = veh.get("occupants", [])

            # Military = Tactical Crimson/Olive; Civilian = Electric Azure/Cyan
            color = (30, 40, 220) if is_mil else (255, 140, 0)

            # Box outline
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Top Badge: Category & ID
            mil_badge = "[MILITARY FORCE] " if is_mil else ""
            v_title = f"{mil_badge}{cat} #{track_id}"
            if occupants:
                v_title += f" (Occupants: {len(occupants)})"

            (tw, th), _ = cv2.getTextSize(v_title, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 2)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 8)), (x1 + tw + 6, y1), color, -1)
            cv2.putText(annotated, v_title, (x1 + 3, max(0, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)

            # Bottom Badge: Number Plate & Country
            if plate:
                plate_badge = f"PLATE [{country}]: {plate}"
                (ptw, pth), _ = cv2.getTextSize(plate_badge, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                py1 = min(h - 5, y2 + pth + 8)
                cv2.rectangle(annotated, (x1, y2), (x1 + ptw + 8, py1), (15, 15, 15), -1)
                cv2.rectangle(annotated, (x1, y2), (x1 + ptw + 8, py1), (0, 215, 255), 1)
                cv2.putText(annotated, plate_badge, (x1 + 4, py1 - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)

        # ---------------------------------------------------------
        # 2. RENDER HUMANS, SKELETON & ACTION BADGES
        # ---------------------------------------------------------
        for p in persons:
            x1, y1, x2, y2 = p["box"]
            track_id = p["track_id"]
            conf = p["conf"]
            action = p["action"]
            role = p["role"]
            face_name = p.get("face_name")

            # In-vehicle occupant vs Pedestrian
            is_in_veh = p["in_vehicle_id"] is not None
            p_color = (0, 220, 255) if is_in_veh else (0, 240, 80)

            cv2.rectangle(annotated, (x1, y1), (x2, y2), p_color, 2)

            # Skeleton
            if p.get("keypoints"):
                draw_skeleton(annotated, p["keypoints"], p.get("keypoints_conf"))

            # Person Title
            identity_str = f" | {face_name}" if face_name else ""
            p_title = f"Person #{track_id}{identity_str} ({conf:.2f})"
            (tw, th), _ = cv2.getTextSize(p_title, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 2)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 8)), (x1 + tw + 6, y1), p_color, -1)
            cv2.putText(annotated, p_title, (x1 + 3, max(0, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, (20, 20, 20), 2, cv2.LINE_AA)

            # Action & Role Subtitle
            sub_text = f"{role} | Act: {action}"
            (stw, sth), _ = cv2.getTextSize(sub_text, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 1)
            cv2.rectangle(annotated, (x1, y1 + 2), (x1 + stw + 6, y1 + sth + 6), (20, 20, 20), -1)
            cv2.putText(annotated, sub_text, (x1 + 3, y1 + sth + 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 200), 1, cv2.LINE_AA)

        # ---------------------------------------------------------
        # 3. RENDER FACE MESHES & IDENTITIES
        # ---------------------------------------------------------
        annotated = self.face_tracker.draw(annotated, tracked_faces, draw_mesh=self.draw_mesh)

        # ---------------------------------------------------------
        # 4. HUD DASHBOARD OVERLAY
        # ---------------------------------------------------------
        if self.show_hud:
            overlay_hud = annotated.copy()
            cv2.rectangle(overlay_hud, (10, 10), (460, 105), (10, 10, 10), -1)
            cv2.addWeighted(overlay_hud, 0.70, annotated, 0.30, 0, annotated)

            hud_line1 = f"FPS: {fps:4.1f} | Persons: {len(persons)} | Vehicles: {len(vehicles)}"
            hud_line2 = f"Faces: {len(tracked_faces)} | ALPR Active: {_HAS_EASYOCR} | Mesh: {self.draw_mesh}"
            mil_count = sum(1 for v in vehicles if v.get("is_military"))
            hud_line3 = f"Military Force Vehicles: {mil_count} | Keys: [Q]uit [R]ec [S]hot [M]esh [H]ud"

            cv2.putText(annotated, hud_line1, (18, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(annotated, hud_line2, (18, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 240, 255), 1, cv2.LINE_AA)
            cv2.putText(annotated, hud_line3, (18, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 200, 100), 1, cv2.LINE_AA)

        return annotated


# ==============================================================================
# MAIN RUN LOOP & CLI INTERFACE
# ==============================================================================
def run_pipeline(source=0, imgsz=640, conf_thresh=0.25, target_fps=60, record=False, save_photos=False):
    pipeline = ComprehensiveAIPipeline(conf_thresh=conf_thresh, imgsz=imgsz)
    cap = ThreadedCamera(source, target_fps=target_fps)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")

    stats = AccuracyStats()
    photo_saver = AsyncPhotoSaver() if save_photos else None

    # Video Recorder
    video_writer = None
    is_recording = record
    if is_recording:
        rec_path = os.path.join(RECORDINGS_DIR, f"rec_{_timestamp_str()}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video_writer = cv2.VideoWriter(rec_path, fourcc, 30.0, (cap.width, cap.height))
        print(f"[INFO] Started recording to: {rec_path}")

    prev_time = time.time()
    print("\n" + "=" * 65)
    print("  MULTI-TASK AI SYSTEM: HUMAN + VEHICLE + ALPR + POSE + FACE")
    print("=" * 65)
    print("  Controls:")
    print("    'q' - Quit")
    print("    'r' - Toggle Video Recording")
    print("    's' - Save Instant Screenshot")
    print("    'p' - Toggle Auto Photo Capture")
    print("    'm' - Toggle Facial Landmark Mesh")
    print("    'h' - Toggle Stats HUD")
    print("=" * 65 + "\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            # Process frame through full multi-task pipeline
            persons, vehicles, tracked_faces = pipeline.process_frame(frame)

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            stats.update(persons, vehicles, fps)

            # Auto-save crops if enabled
            if photo_saver:
                for p in persons:
                    photo_saver.request_save(frame, p["box"], f"person_{p['action']}", p["track_id"])
                for v in vehicles:
                    v_label = f"{v['category']}_{v.get('plate', 'noplate')}"
                    photo_saver.request_save(frame, v["box"], v_label, v["track_id"])

            # Render overlay
            annotated = pipeline.render_overlay(frame, persons, vehicles, tracked_faces, stats=stats, fps=fps)

            # Record if active
            if is_recording and video_writer is not None:
                video_writer.write(annotated)
                cv2.circle(annotated, (cap.width - 25, 25), 8, (0, 0, 255), -1)

            cv2.imshow("Multi-Task AI: Human Pose & Action + Vehicle & ALPR + Face Re-ID", annotated)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("r"):
                is_recording = not is_recording
                if is_recording:
                    rec_path = os.path.join(RECORDINGS_DIR, f"rec_{_timestamp_str()}.mp4")
                    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                    video_writer = cv2.VideoWriter(rec_path, fourcc, 30.0, (annotated.shape[1], annotated.shape[0]))
                    print(f"[INFO] Started recording to: {rec_path}")
                else:
                    if video_writer:
                        video_writer.release()
                        video_writer = None
                    print("[INFO] Stopped recording.")
            elif key == ord("s"):
                shot_path = os.path.join(RECORDINGS_DIR, f"shot_{_timestamp_str()}.jpg")
                cv2.imwrite(shot_path, annotated)
                print(f"[INFO] Saved screenshot: {shot_path}")
            elif key == ord("p"):
                if photo_saver is None:
                    photo_saver = AsyncPhotoSaver()
                    print("[INFO] Auto Photo Capture: ENABLED")
                else:
                    photo_saver.stop()
                    photo_saver = None
                    print("[INFO] Auto Photo Capture: DISABLED")
            elif key == ord("m"):
                pipeline.draw_mesh = not pipeline.draw_mesh
                print(f"[INFO] Face Landmark Mesh: {'ENABLED' if pipeline.draw_mesh else 'DISABLED'}")
            elif key == ord("h"):
                pipeline.show_hud = not pipeline.show_hud

    finally:
        cap.release()
        if video_writer:
            video_writer.release()
        if photo_saver:
            photo_saver.stop()
        cv2.destroyAllWindows()
        print(f"\n[INFO] Session Finished. Total Frames: {stats.total_frames}, Avg FPS: {stats.avg_fps:.1f}")


def main():
    parser = argparse.ArgumentParser(description="Multi-Task AI: Human Pose & Action + Vehicle & ALPR + Face Re-ID")
    parser.add_argument("--source", default="0", help="Video source (0 for webcam, or video file path)")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image resolution (e.g. 640, 480, 320)")
    parser.add_argument("--conf", type=float, default=0.25, help="Detection confidence threshold (default: 0.25)")
    parser.add_argument("--fps", type=int, default=60, help="Target camera grab FPS")
    parser.add_argument("--record", action="store_true", help="Start recording video automatically")
    parser.add_argument("--photos", action="store_true", help="Start saving photo crops automatically")
    args = parser.parse_args()

    # Convert numeric camera string to integer
    src = int(args.source) if str(args.source).isdigit() else args.source
    run_pipeline(source=src, imgsz=args.imgsz, conf_thresh=args.conf, target_fps=args.fps, record=args.record, save_photos=args.photos)


if __name__ == "__main__":
    main()