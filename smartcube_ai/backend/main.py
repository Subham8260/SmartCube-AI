from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import cv2
import base64
import numpy as np

from vision import extract_tiles
from ai_color import predict_colors
from solver import solve_cube
from validator import validate_cube

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanAllRequest(BaseModel):
    images: List[str]

class SolveRequest(BaseModel):
    cube_faces: List[List[str]]

@app.post("/scan-all")
def scan_all_faces(req: ScanAllRequest):
    cube_faces = []

    for img_b64 in req.images:
        img_bytes = base64.b64decode(img_b64)
        img_np = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        tiles = extract_tiles(frame)
        colors = predict_colors(tiles)

        if not isinstance(colors, list) or len(colors) != 9:
            colors = ["white"] * 9

        cube_faces.append(colors)

    while len(cube_faces) < 6:
        cube_faces.append(["white"] * 9)

    for i in range(6):
        if len(cube_faces[i]) != 9:
            cube_faces[i] = ["white"] * 9

    return {"cube_faces": cube_faces}

@app.post("/solve")
def solve(req: SolveRequest):
    valid, msg, fixed_faces = validate_cube(req.cube_faces)

    while len(fixed_faces) < 6:
        fixed_faces.append(["white"] * 9)
    for i in range(6):
        if len(fixed_faces[i]) != 9:
            fixed_faces[i] = ["white"] * 9

    try:
        steps = solve_cube(fixed_faces)
        return {"success": True, "message": msg, "faces": fixed_faces, "steps": steps}
    except Exception as e:
        return {"success": False, "error": str(e)}
