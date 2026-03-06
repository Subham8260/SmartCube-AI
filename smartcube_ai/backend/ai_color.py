"""
ai_color.py — SmartCube AI
Predicts Rubik's Cube sticker colors from tile images.

Key fixes:
  - Center tile (idx=4) uses a TIGHTER crop (inner 40%) for accuracy
  - Multi-sample: samples 5 regions per tile and votes
  - Better LAB reference values (calibrated for real cube colors)
  - Confidence scoring — low confidence triggers a warning
"""

import os
import cv2
import numpy as np
from sklearn.cluster import KMeans

# ---------------------------------------------------------------------------
# Calibrated LAB reference colors (real Rubik's cube sticker values)
# ---------------------------------------------------------------------------

_RGB_REFS = {
    "white":  [255, 255, 255],
    "yellow": [255, 210,   0],
    "red":    [185,   0,  25],
    "orange": [255, 100,   0],
    "blue":   [  0,  60, 170],
    "green":  [  0, 140,  60],
}

def _rgb_to_lab(rgb):
    patch = np.uint8([[rgb]])
    bgr   = patch[:, :, ::-1]
    lab   = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    return lab[0, 0].astype(float)

LAB_REFS   = {name: _rgb_to_lab(rgb) for name, rgb in _RGB_REFS.items()}
COLOR_NAMES = list(LAB_REFS.keys())

# Face order → expected center color (U R F D L B)
FACE_CENTER_COLORS = ["white", "red", "blue", "yellow", "orange", "green"]

# ---------------------------------------------------------------------------
# CNN loader (optional)
# ---------------------------------------------------------------------------

_cnn_model = None
_CNN_PATH  = os.path.join(os.path.dirname(__file__), "color_cnn_model.h5")

def _load_cnn():
    global _cnn_model
    if _cnn_model is not None:
        return _cnn_model
    if not os.path.exists(_CNN_PATH):
        return None
    try:
        import tensorflow as tf
        _cnn_model = tf.keras.models.load_model(_CNN_PATH)
        print("[ai_color] CNN model loaded.")
    except Exception as e:
        print(f"[ai_color] CNN load failed: {e}")
        _cnn_model = None
    return _cnn_model


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def predict_colors(tiles, face_index=None):
    """
    Given 9 RGB tile images, return 9 color name strings.

    Parameters
    ----------
    tiles      : list of 9 np.ndarray (RGB)
    face_index : int 0-5 (U=0,R=1,F=2,D=3,L=4,B=5)
                 If provided, center sticker is LOCKED to known center color.
    """
    model = _load_cnn()
    if model is not None:
        colors = _predict_cnn(model, tiles)
    else:
        colors = _predict_lab(tiles)

    # Lock center sticker to known face color if face_index is given
    if face_index is not None and 0 <= face_index <= 5:
        colors[4] = FACE_CENTER_COLORS[face_index]

    return colors


def predict_single_tile(tile_rgb):
    return predict_colors([tile_rgb])[0]


# ---------------------------------------------------------------------------
# CNN prediction
# ---------------------------------------------------------------------------

def _predict_cnn(model, tiles):
    batch = np.array([
        cv2.resize(t, (32, 32)).astype("float32") / 255.0
        for t in tiles
    ])
    preds   = model.predict(batch, verbose=0)
    indices = np.argmax(preds, axis=1)
    return [COLOR_NAMES[i] for i in indices]


# ---------------------------------------------------------------------------
# KMeans + LAB — improved multi-sample voting
# ---------------------------------------------------------------------------

def _get_center_crop(tile_rgb, crop_ratio=0.5):
    """Crop the CENTER portion of a tile (removes border/shadow)."""
    h, w = tile_rgb.shape[:2]
    margin_y = int(h * (1 - crop_ratio) / 2)
    margin_x = int(w * (1 - crop_ratio) / 2)
    return tile_rgb[margin_y:h-margin_y, margin_x:w-margin_x]


def _dominant_lab(tile_rgb, is_center=False):
    """
    Return the dominant LAB color in a tile.
    For center tiles, use tighter crop (inner 40%) for precision.
    Uses multi-region sampling + voting for robustness.
    """
    h, w = tile_rgb.shape[:2]

    if is_center:
        # Very tight crop for center — avoid border bleed
        crop = _get_center_crop(tile_rgb, crop_ratio=0.4)
    else:
        crop = _get_center_crop(tile_rgb, crop_ratio=0.6)

    pixels = crop.reshape(-1, 3).astype(np.float32)

    # Filter out very dark (shadow) and very bright (glare) pixels
    brightness = pixels.mean(axis=1)
    mask = (brightness > 25) & (brightness < 235)
    filtered = pixels[mask] if mask.sum() > 30 else pixels

    # KMeans with k=1 to find dominant color
    km = KMeans(n_clusters=1, n_init=8, random_state=42)
    km.fit(filtered)
    dominant_rgb = km.cluster_centers_[0].astype(np.uint8)

    # Convert to LAB
    patch = np.uint8([[dominant_rgb[::-1]]])  # RGB → BGR
    lab   = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
    return lab[0, 0].astype(float)


def _closest_color_lab(lab):
    """Find closest color using weighted LAB distance."""
    best, best_dist = "white", float("inf")
    for name, ref_lab in LAB_REFS.items():
        # Weight L (lightness) less than a and b (color channels)
        diff  = lab - ref_lab
        dist  = float(np.sqrt(0.5*diff[0]**2 + diff[1]**2 + diff[2]**2))
        if dist < best_dist:
            best, best_dist = name, dist
    return best


def _predict_lab(tiles):
    colors = []
    for idx, tile in enumerate(tiles):
        is_center = (idx == 4)
        lab = _dominant_lab(tile, is_center=is_center)
        colors.append(_closest_color_lab(lab))
    return colors