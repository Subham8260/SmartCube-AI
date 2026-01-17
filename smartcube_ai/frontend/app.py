import sys
import os
import base64

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import requests
from backend.cube_visual import draw_cube

API_URL = "http://127.0.0.1:9000"

st.title("🧠 SmartCube AI – Rubik’s Cube Solver")

if "faces" not in st.session_state:
    st.session_state.faces = []

mode = st.radio("Select input method", ["Camera", "Upload Images"])

if mode == "Camera":
    img = st.camera_input("Capture cube face")
    if img:
        st.session_state.faces.append(img)

else:
    imgs = st.file_uploader(
        "Upload 6 cube faces",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )
    if imgs:
        st.session_state.faces = imgs

st.write("Faces uploaded:", len(st.session_state.faces))
for i, f in enumerate(st.session_state.faces):
    st.image(f, caption=f"Face {i+1}", width=120)

if st.button("Analyze & Solve"):
    if len(st.session_state.faces) != 6:
        st.warning("Upload exactly 6 cube faces")
    else:
        images_b64 = [
            base64.b64encode(f.getvalue()).decode()
            for f in st.session_state.faces
        ]

        scan_res = requests.post(
            f"{API_URL}/scan-all",
            json={"images": images_b64}
        ).json()

        cube_faces = scan_res.get("cube_faces")
        if not cube_faces:
            st.error("Cube scanning failed")
            st.stop()

        st.subheader("Detected Cube State")
        draw_cube(cube_faces)

        solve_res = requests.post(
            f"{API_URL}/solve",
            json={"cube_faces": cube_faces}
        ).json()

        steps = solve_res.get("steps")
        if steps:
            st.subheader("Solution Steps")
            for i, step in enumerate(steps, 1):
                st.write(f"Step {i}: {step}")
        else:
            st.error(solve_res.get("error", "Solver failed"))
