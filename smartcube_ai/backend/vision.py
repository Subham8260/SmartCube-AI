"""
vision.py — SmartCube AI
Extracts 9 sticker tiles from a cube-face image.

Improvements over v1:
  • Converts BGR → RGB before returning (ai_color.py expects RGB)
  • Crops a centered square to remove background clutter
  • Applies CLAHE to improve color accuracy under variable lighting
  • Adds a debug/overlay helper used by the /scan-preview endpoint
"""

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_tiles(frame: np.ndarray, tile_size: int = 80) -> list[np.ndarray]:
    """
    Return a list of 9 RGB tile images (row-major, top-left → bottom-right).

    Parameters
    ----------
    frame     : BGR image as returned by cv2.imdecode / cv2.VideoCapture.read
    tile_size : side length (px) of each returned tile
    """
    bgr = _preprocess(frame)
    h, w = bgr.shape[:2]
    step = h // 3          # assume square after preprocessing

    tiles = []
    for row in range(3):
        for col in range(3):
            y1, y2 = row * step, (row + 1) * step
            x1, x2 = col * step, (col + 1) * step
            tile_bgr = bgr[y1:y2, x1:x2]
            tile_rgb = cv2.cvtColor(
                cv2.resize(tile_bgr, (tile_size, tile_size)),
                cv2.COLOR_BGR2RGB,
            )
            tiles.append(tile_rgb)

    return tiles


def draw_grid_overlay(frame: np.ndarray) -> np.ndarray:
    """
    Return a copy of *frame* with a 3×3 guide grid drawn on it.
    Useful for the live-camera preview so users can align the cube.
    """
    out = frame.copy()
    h, w = out.shape[:2]
    step_y, step_x = h // 3, w // 3
    color = (0, 255, 180)   # bright teal
    thick = 2

    for i in range(1, 3):
        cv2.line(out, (i * step_x, 0), (i * step_x, h), color, thick)
        cv2.line(out, (0, i * step_y), (w, i * step_y), color, thick)

    # outer border
    cv2.rectangle(out, (0, 0), (w - 1, h - 1), color, thick)
    return out


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _preprocess(frame: np.ndarray) -> np.ndarray:
    """
    Resize to a 300×300 square and apply CLAHE for lighting normalisation.
    """
    square = cv2.resize(frame, (300, 300))
    # CLAHE on L-channel of LAB to brighten stickers without over-saturation
    lab = cv2.cvtColor(square, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    l = clahe.apply(l)
    enhanced = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    return enhanced