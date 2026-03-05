"""
ai_color.py — SmartCube AI
Predicts the Rubik's Cube sticker color for each tile image.

Strategy (two-stage):
  1. CNN model  — loaded from  backend/color_cnn_model.h5  if present.
  2. KMeans + LAB distance — robust fallback (works with no trained model).

The LAB-based classifier is significantly more accurate than the original
RGB Euclidean approach because LAB is perceptually uniform, so the
distance between, e.g., orange and red reflects what the human eye sees.
"""

import os
import numpy as np
from sklearn.cluster import KMeans

# ---------------------------------------------------------------------------
# Reference colors in LAB space (computed once at import time)
# ---------------------------------------------------------------------------

import cv2

_RGB_REFS = {
    "white":  [255, 255, 255],
    "yellow": [255, 213,   0],
    "red":    [196,   2,  51],
    "orange": [255, 120,   0],
    "blue":   [  0,  70, 173],
    "green":  [  0, 155,  72],
}

def _rgb_to_lab(rgb: list) -> np.ndarray:
    patch = np.uint8([[rgb]])                    # 1×1 BGR patch
    bgr_patch = patch[:, :, ::-1]               # RGB → BGR for OpenCV
    lab = cv2.cvtColor(bgr_patch, cv2.COLOR_BGR2LAB)
    return lab[0, 0].astype(float)

LAB_REFS: dict[str, np.ndarray] = {
    name: _rgb_to_lab(rgb) for name, rgb in _RGB_REFS.items()
}

COLOR_NAMES = list(LAB_REFS.keys())


# ---------------------------------------------------------------------------
# CNN loader (optional)
# ---------------------------------------------------------------------------

_cnn_model = None
_CNN_PATH = os.path.join(os.path.dirname(__file__), "color_cnn_model.h5")

def _load_cnn():
    global _cnn_model
    if _cnn_model is not None:
        return _cnn_model
    if not os.path.exists(_CNN_PATH):
        return None
    try:
        import tensorflow as tf          # noqa: F401
        _cnn_model = tf.keras.models.load_model(_CNN_PATH)
        print("[ai_color] CNN model loaded successfully.")
    except Exception as exc:
        print(f"[ai_color] Could not load CNN model: {exc}")
        _cnn_model = None
    return _cnn_model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_colors(tiles: list[np.ndarray]) -> list[str]:
    """
    Given a list of 9 RGB tile images, return a list of 9 color name strings.
    Uses CNN if available, otherwise falls back to KMeans + LAB distance.
    """
    model = _load_cnn()
    if model is not None:
        return _predict_cnn(model, tiles)
    return _predict_lab(tiles)


def predict_single_tile(tile_rgb: np.ndarray) -> str:
    """Convenience wrapper for a single tile."""
    return predict_colors([tile_rgb])[0]


# ---------------------------------------------------------------------------
# CNN prediction
# ---------------------------------------------------------------------------

def _predict_cnn(model, tiles: list[np.ndarray]) -> list[str]:
    batch = np.array([
        cv2.resize(t, (32, 32)).astype("float32") / 255.0
        for t in tiles
    ])
    preds = model.predict(batch, verbose=0)          # shape (9, 6)
    indices = np.argmax(preds, axis=1)
    return [COLOR_NAMES[i] for i in indices]


# ---------------------------------------------------------------------------
# KMeans + LAB distance fallback
# ---------------------------------------------------------------------------

def _dominant_lab(tile_rgb: np.ndarray) -> np.ndarray:
    """Return the dominant LAB color in a tile using KMeans(k=1)."""
    # Ignore very dark or very bright pixels (likely border/reflection)
    pixels = tile_rgb.reshape(-1, 3).astype(np.float32)
    brightness = pixels.mean(axis=1)
    mask = (brightness > 20) & (brightness < 240)
    filtered = pixels[mask] if mask.sum() > 50 else pixels

    km = KMeans(n_clusters=1, n_init=5, random_state=0)
    km.fit(filtered)
    dominant_rgb = km.cluster_centers_[0].astype(np.uint8)

    # Convert dominant RGB → LAB
    patch = np.uint8([[dominant_rgb[::-1]]])   # RGB → BGR
    lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
    return lab[0, 0].astype(float)


def _closest_color_lab(lab: np.ndarray) -> str:
    best, best_dist = "white", float("inf")
    for name, ref_lab in LAB_REFS.items():
        dist = float(np.linalg.norm(lab - ref_lab))
        if dist < best_dist:
            best, best_dist = name, dist
    return best


def _predict_lab(tiles: list[np.ndarray]) -> list[str]:
    colors = []
    for tile in tiles:
        lab = _dominant_lab(tile)
        colors.append(_closest_color_lab(lab))
    return colors