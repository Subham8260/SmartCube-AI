"""
main.py — SmartCube AI  FastAPI Backend
=======================================

Endpoints
---------
POST /scan-all          Scan 1-6 base64 face images → detected colors
POST /scan-frame        Scan a single base64 frame → 9 colors + overlay image
POST /solve             Validate cube state → Kociemba solution
POST /scramble          Return a random scramble + resulting cube state
GET  /health            Health-check
"""

import base64
import io

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from vision    import extract_tiles, draw_grid_overlay
from ai_color  import predict_colors
from solver    import solve_cube
from validator import validate_cube, state_dict_to_list, state_list_to_dict
from cube_logic import scramble as generate_scramble, apply_moves, solved_state

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SmartCube AI",
    description="AI-powered Rubik's Cube solver — computer vision + Kociemba algorithm",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ScanAllRequest(BaseModel):
    images: List[str]           # list of base64-encoded images (1–6)

class ScanFrameRequest(BaseModel):
    image: str                  # single base64 frame (live camera)
    draw_overlay: bool = True   # return annotated preview image
    face_index: Optional[int] = None  # 0=U,1=R,2=F,3=D,4=L,5=B — locks center color

class SolveRequest(BaseModel):
    cube_faces: List[List[str]] # 6 faces × 9 colors

class ScrambleRequest(BaseModel):
    moves: int = 20             # number of scramble moves


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decode_image(b64: str) -> np.ndarray:
    """Decode a base64 image string to a BGR numpy array."""
    # Strip data-URL prefix if present
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    raw = base64.b64decode(b64)
    arr = np.frombuffer(raw, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image — invalid format.")
    return frame


def _encode_image(frame: np.ndarray) -> str:
    """Encode a BGR numpy array to a base64 JPEG string."""
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return base64.b64encode(buf).decode()


def _safe_colors(colors) -> List[str]:
    """Ensure exactly 9 valid color strings."""
    valid = {"white","yellow","red","orange","blue","green"}
    if not isinstance(colors, list) or len(colors) != 9:
        return ["white"] * 9
    return [c if c in valid else "white" for c in colors]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/scan-all")
def scan_all_faces(req: ScanAllRequest):
    """
    Accept up to 6 base64 face images.
    Returns detected 9-color list for each face.
    """
    cube_faces: List[List[str]] = []

    for idx, img_b64 in enumerate(req.images[:6]):
        try:
            frame  = _decode_image(img_b64)
            tiles  = extract_tiles(frame)
            colors = predict_colors(tiles, face_index=idx)   # locks center
            cube_faces.append(_safe_colors(colors))
        except Exception as exc:
            # Don't crash — return placeholder and flag the issue
            cube_faces.append(["white"] * 9)
            print(f"[scan-all] face {idx} error: {exc}")

    # Pad to 6 faces
    defaults = ["white","red","blue","yellow","orange","green"]
    while len(cube_faces) < 6:
        i = len(cube_faces)
        cube_faces.append([defaults[i]] * 9)

    return {"cube_faces": cube_faces, "faces_received": len(req.images)}


@app.post("/scan-frame")
def scan_single_frame(req: ScanFrameRequest):
    """
    Scan a single live-camera frame.
    Returns detected colors + (optionally) an annotated preview image.
    Accepts optional face_index (0-5) to lock center color.
    """
    face_index = getattr(req, "face_index", None)

    try:
        frame  = _decode_image(req.image)
        tiles  = extract_tiles(frame)
        colors = predict_colors(tiles, face_index=face_index)
        colors = _safe_colors(colors)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    result: dict = {"colors": colors}

    if req.draw_overlay:
        resized = cv2.resize(frame, (360, 360))
        overlay = draw_grid_overlay(resized)
        h, w    = overlay.shape[:2]
        step    = h // 3

        # BGR color fills for each detected color
        color_map_bgr = {
            "white":  (240, 240, 235),
            "yellow": (  0, 210, 255),
            "red":    (  0,   0, 200),
            "orange": (  0, 120, 255),
            "blue":   (200,  70,   0),
            "green":  (  0, 155,  50),
        }

        for row in range(3):
            for col in range(3):
                idx   = row * 3 + col
                x1    = col * step + 6
                y1    = row * step + 6
                x2    = x1 + step - 12
                y2    = y1 + step - 12
                c_bgr = color_map_bgr.get(colors[idx], (128, 128, 128))

                # Filled rounded square
                cv2.rectangle(overlay, (x1, y1), (x2, y2), c_bgr, -1)
                # Dark border
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), 2)

                # Sticker number label
                cx = x1 + (x2 - x1) // 2
                cy = y1 + (y2 - y1) // 2
                cv2.putText(overlay, str(idx+1),
                            (cx - 6, cy + 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            (0, 0, 0), 2)

                # Mark center with star
                if idx == 4:
                    cv2.putText(overlay, "*",
                                (cx + 8, cy - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                                (0, 255, 204), 2)

        result["preview"] = _encode_image(overlay)

    return result


@app.post("/solve")
def solve(req: SolveRequest):
    """
    Validate cube state and return Kociemba solution steps.
    """
    valid, msg, fixed_faces = validate_cube(req.cube_faces)

    if not valid:
        return {
            "success": False,
            "error": msg,
            "faces": fixed_faces,
            "steps": [],
        }

    try:
        steps = solve_cube(fixed_faces)
        return {
            "success":    True,
            "message":    msg,
            "faces":      fixed_faces,
            "steps":      steps,
            "move_count": len(steps),
        }
    except Exception as exc:
        return {
            "success": False,
            "error":   str(exc),
            "faces":   fixed_faces,
            "steps":   [],
        }


@app.post("/scramble")
def scramble_cube(req: ScrambleRequest):
    """
    Generate a random scramble.
    Returns the scramble move list + resulting cube face state.
    """
    n = max(5, min(req.moves, 30))
    state, moves = generate_scramble(n)
    faces = state_dict_to_list(state)
    return {
        "scramble_moves": moves,
        "cube_faces": faces,
        "move_count": len(moves),
    }


@app.post("/apply-moves")
def apply_moves_endpoint(req: dict):
    """
    Apply a list of moves to a given cube state.
    Body: { "cube_faces": [...], "moves": ["R","U","R'","U'"] }
    """
    faces = req.get("cube_faces", [])
    moves = req.get("moves", [])

    if len(faces) != 6:
        raise HTTPException(status_code=422, detail="cube_faces must have 6 faces.")

    state = state_list_to_dict(faces)
    try:
        new_state = apply_moves(state, moves)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return {"cube_faces": state_dict_to_list(new_state)}