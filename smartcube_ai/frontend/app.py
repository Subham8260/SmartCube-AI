"""
app.py — SmartCube AI  Streamlit Frontend
Run:  streamlit run frontend/app.py
"""

import sys, os, base64
from typing import Optional, List
import requests
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from cube_visual import show_cube_2d, show_cube_3d, cube_to_ascii

API_URL      = os.environ.get("SMARTCUBE_API", "http://127.0.0.1:9000")
VALID_COLORS = ["white","yellow","red","orange","blue","green"]
COLOR_HEX    = {"white":"#f5f5f0","yellow":"#ffd600","red":"#e53935",
                "orange":"#fb8c00","blue":"#1e88e5","green":"#43a047"}
FACE_LABELS  = ["U","R","F","D","L","B"]
FACE_NAMES   = {"U":"Up","R":"Right","F":"Front","D":"Down","L":"Left","B":"Back"}
FACE_CENTERS = {"U":"white","R":"red","F":"blue","D":"yellow","L":"orange","B":"green"}

st.set_page_config(page_title="SmartCube AI", page_icon="🧊",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:#0a0a0f;color:#e8e8f0;}
.block-container{padding-top:1.2rem;}
.move-chip{display:inline-block;padding:5px 11px;margin:3px;
  background:#1a1a26;border:1px solid #2a2a3d;border-radius:8px;
  font-family:monospace;font-size:.88rem;font-weight:700;color:#e8e8f0;}
.move-chip.current{background:rgba(0,255,204,.15);border-color:#00ffcc;color:#00ffcc;}
.move-chip.done{opacity:.32;text-decoration:line-through;}
.sec{font-size:.6rem;letter-spacing:2px;text-transform:uppercase;color:#6b6b8a;margin-bottom:.4rem;}
.grid-cell-label{text-align:center;font-size:.65rem;color:#888;margin-bottom:2px;}
#MainMenu,footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
def _default_faces():
    return {f: [FACE_CENTERS[f]]*9 for f in FACE_LABELS}

for k, v in [("faces",_default_faces()),("sel_color","white"),
             ("sel_face","U"),("solution",[]),("step",0),
             ("cam_edit_face", None), ("upload_edit_face", None),
             ("cam_edit_color","white"), ("upload_edit_color","white")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── API helpers ────────────────────────────────────────────────────────────────
def api(endpoint, payload):
    try:
        r = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error ({endpoint}): {e}")
        return None

def faces_to_list():
    return [st.session_state.faces[f] for f in FACE_LABELS]

def list_to_faces(lst):
    return {FACE_LABELS[i]: lst[i] for i in range(6)}

# ── Reusable manual correction grid ───────────────────────────────────────────
def render_correction_grid(face_label: str, key_prefix: str, edit_color_key: str):
    """
    Renders a 3×3 interactive grid for a given face with a color picker.
    key_prefix: unique string to avoid Streamlit key collisions (e.g. 'cam', 'upl')
    edit_color_key: session_state key for the active paint color
    """
    st.markdown(f"<div class='sec'>✏️ Correct Face {face_label} — {FACE_NAMES[face_label]}</div>",
                unsafe_allow_html=True)

    # Color picker row
    st.markdown("<div class='sec'>Pick color to paint:</div>", unsafe_allow_html=True)
    pal_cols = st.columns(6)
    for i, color in enumerate(VALID_COLORS):
        with pal_cols[i]:
            active = st.session_state[edit_color_key] == color
            border = "3px solid #00ffcc" if active else "2px solid #2a2a3d"
            st.markdown(
                f"<div style='width:100%;height:28px;border-radius:6px;"
                f"background:{COLOR_HEX[color]};border:{border};margin-bottom:4px;'></div>",
                unsafe_allow_html=True)
            if st.button(color[0].upper(), key=f"{key_prefix}_pal_{color}",
                         use_container_width=True,
                         help=color.capitalize()):
                st.session_state[edit_color_key] = color
                st.rerun()

    st.markdown("<div class='sec' style='margin-top:8px;'>Click sticker to change color:</div>",
                unsafe_allow_html=True)

    face_data = st.session_state.faces[face_label]
    changed = False
    for row in range(3):
        row_cols = st.columns(3)
        for col in range(3):
            idx = row*3 + col
            color = face_data[idx]
            is_center = (idx == 4)
            with row_cols[col]:
                # Color block above button
                st.markdown(
                    f"<div style='height:18px;border-radius:5px 5px 0 0;"
                    f"background:{COLOR_HEX[color]};"
                    f"border:2px solid {'#00ffcc' if is_center else '#333'};'></div>",
                    unsafe_allow_html=True)
                lbl = "●" if is_center else color[0].upper()
                if st.button(lbl, key=f"{key_prefix}_cell_{face_label}_{idx}",
                             disabled=is_center,
                             use_container_width=True,
                             help="Center — fixed" if is_center else f"Set → {st.session_state[edit_color_key]}"):
                    st.session_state.faces[face_label][idx] = st.session_state[edit_color_key]
                    changed = True

    if changed:
        st.rerun()

    # Quick action buttons
    qa1, qa2 = st.columns(2)
    with qa1:
        if st.button(f"Fill all → {st.session_state[edit_color_key]}",
                     key=f"{key_prefix}_fill_{face_label}", use_container_width=True):
            for i in range(9):
                if i != 4:
                    st.session_state.faces[face_label][i] = st.session_state[edit_color_key]
            st.rerun()
    with qa2:
        if st.button("Reset face", key=f"{key_prefix}_reset_{face_label}",
                     use_container_width=True):
            st.session_state.faces[face_label] = [FACE_CENTERS[face_label]]*9
            st.rerun()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧊 SmartCube AI")
    page = st.radio("Navigate", ["🧩 Solver","ℹ️ About"], label_visibility="collapsed")
    st.divider()
    st.markdown("<div class='sec'>Backend Status</div>", unsafe_allow_html=True)
    try:
        hc = requests.get(f"{API_URL}/health", timeout=3)
        st.success("✅ API online") if hc.ok else st.error("❌ API error")
    except Exception:
        st.error("❌ API offline\nRun: uvicorn main:app --port 9000")
    st.divider()
    st.markdown("<div class='sec'>Cube Debug</div>", unsafe_allow_html=True)
    st.code(cube_to_ascii(faces_to_list()), language=None)


# ═════════════════════════════════════════════════════════════════════════════
# SOLVER PAGE
# ═════════════════════════════════════════════════════════════════════════════
if "Solver" in page:

    c1, c2 = st.columns([3,1])
    with c1:
        st.markdown("# 🧊 SmartCube AI")
        st.caption("AI-Powered Rubik's Cube Solver · Kociemba Algorithm · Computer Vision")
    with c2:
        view3d = st.toggle("3D View", value=False)

    st.divider()
    tab1, tab2, tab3 = st.tabs(["🎨 Manual Input", "📁 Upload Images", "📷 Live Camera"])

    # ── TAB 1: MANUAL ─────────────────────────────────────────────────────────
    with tab1:
        col_pal, col_edit, col_prev = st.columns([1, 1.4, 2.2])

        with col_pal:
            st.markdown("<div class='sec'>Color Palette</div>", unsafe_allow_html=True)
            for color in VALID_COLORS:
                active = st.session_state.sel_color == color
                border = "3px solid #00ffcc" if active else "2px solid #2a2a3d"
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
                    f"<div style='width:32px;height:32px;border-radius:7px;"
                    f"background:{COLOR_HEX[color]};border:{border};'></div>"
                    f"<span style='color:{'#00ffcc' if active else '#e8e8f0'};font-size:.82rem;'>"
                    f"{'✓ ' if active else ''}{color.capitalize()}</span></div>",
                    unsafe_allow_html=True)
                if st.button(f"Use {color}", key=f"pal_{color}", use_container_width=True):
                    st.session_state.sel_color = color
                    st.rerun()

        with col_edit:
            st.markdown("<div class='sec'>Select Face</div>", unsafe_allow_html=True)
            face_choice = st.radio("face", FACE_LABELS,
                format_func=lambda f: f"{f} — {FACE_NAMES[f]}",
                index=FACE_LABELS.index(st.session_state.sel_face),
                label_visibility="collapsed")
            st.session_state.sel_face = face_choice
            f = face_choice
            st.markdown(f"<div class='sec' style='margin-top:10px;'>Editing: {f} ({FACE_NAMES[f]})</div>",
                        unsafe_allow_html=True)
            face_data = st.session_state.faces[f]
            changed = False
            for row in range(3):
                cols_r = st.columns(3)
                for ci in range(3):
                    idx = row*3 + ci
                    color = face_data[idx]
                    is_center = (idx == 4)
                    with cols_r[ci]:
                        lbl = "●" if is_center else color[0].upper()
                        if st.button(lbl, key=f"s_{f}_{idx}", disabled=is_center,
                                     use_container_width=True,
                                     help="Center — fixed" if is_center else f"Set {st.session_state.sel_color}"):
                            st.session_state.faces[f][idx] = st.session_state.sel_color
                            changed = True
                        st.markdown(
                            f"<div style='height:5px;border-radius:3px;"
                            f"background:{COLOR_HEX[color]};margin-top:-10px;margin-bottom:4px;'></div>",
                            unsafe_allow_html=True)
            ca, cb = st.columns(2)
            with ca:
                if st.button("Fill All", use_container_width=True):
                    for i in range(9):
                        if i != 4:
                            st.session_state.faces[f][i] = st.session_state.sel_color
                    st.rerun()
            with cb:
                if st.button("Reset Face", use_container_width=True):
                    st.session_state.faces[f] = [FACE_CENTERS[f]]*9
                    st.rerun()
            if changed:
                st.rerun()

        with col_prev:
            st.markdown("<div class='sec'>Cube Preview</div>", unsafe_allow_html=True)
            fl = faces_to_list()
            show_cube_3d(fl, "3D View") if view3d else show_cube_2d(fl, "Current State")

    # ── TAB 2: UPLOAD ─────────────────────────────────────────────────────────
    with tab2:
        st.info("Upload **6 photos** of your cube faces in order: **U R F D L B**")

        uploaded = st.file_uploader("Upload cube faces",
            type=["jpg","jpeg","png"], accept_multiple_files=True,
            label_visibility="collapsed")

        if uploaded:
            img_cols = st.columns(min(6, len(uploaded)))
            for i, f_obj in enumerate(uploaded[:6]):
                with img_cols[i]:
                    # Draw grid overlay on uploaded image using OpenCV
                    import cv2, numpy as np
                    file_bytes = np.frombuffer(f_obj.getvalue(), np.uint8)
                    img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    if img_cv is not None:
                        h, w = img_cv.shape[:2]
                        # Draw teal 3x3 grid
                        sy, sx = h//3, w//3
                        for k in range(1,3):
                            cv2.line(img_cv,(k*sx,0),(k*sx,h),(0,255,180),2)
                            cv2.line(img_cv,(0,k*sy),(w,k*sy),(0,255,180),2)
                        cv2.rectangle(img_cv,(0,0),(w-1,h-1),(0,255,180),2)
                        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
                        st.image(img_rgb, caption=f"Face {FACE_LABELS[i]} — {FACE_NAMES[FACE_LABELS[i]]}", use_column_width=True)
                    else:
                        st.image(f_obj, caption=f"Face {FACE_LABELS[i]}", use_column_width=True)

            if st.button("🔍 Detect Colors from Images", type="primary", use_container_width=True):
                with st.spinner("AI analysing cube faces…"):
                    images_b64 = [base64.b64encode(f.getvalue()).decode() for f in uploaded[:6]]
                    result = api("scan-all", {"images": images_b64})
                    if result:
                        st.session_state.faces = list_to_faces(result["cube_faces"])
                        st.session_state.upload_edit_face = FACE_LABELS[0]
                        st.success("✓ Colors detected! Scroll down to correct any mistakes.")
                        st.rerun()

        # ── Detected result + correction grid ─────────────────────────────────
        st.divider()
        upl_c1, upl_c2 = st.columns([1.4, 1])

        with upl_c1:
            st.markdown("<div class='sec'>Detected Cube State</div>", unsafe_allow_html=True)
            show_cube_2d(faces_to_list(), "Detected State")

        with upl_c2:
            st.markdown("<div class='sec'>Select face to correct</div>", unsafe_allow_html=True)
            upl_face = st.selectbox(
                "Face", FACE_LABELS,
                format_func=lambda f: f"{f} — {FACE_NAMES[f]} (center: {FACE_CENTERS[f]})",
                key="upload_face_select")
            st.session_state.upload_edit_face = upl_face

            # Show current detected colors for this face as color swatches
            face_now = st.session_state.faces[upl_face]
            st.markdown("<div class='sec'>Current detection:</div>", unsafe_allow_html=True)
            swatch_cols = st.columns(3)
            for idx in range(9):
                with swatch_cols[idx % 3]:
                    c = face_now[idx]
                    st.markdown(
                        f"<div style='height:22px;border-radius:4px;"
                        f"background:{COLOR_HEX[c]};margin-bottom:2px;"
                        f"border:1px solid #333;'></div>",
                        unsafe_allow_html=True)

            st.divider()
            render_correction_grid(upl_face, "upl", "upload_edit_color")

    # ── TAB 3: CAMERA ─────────────────────────────────────────────────────────
    with tab3:
        st.markdown("""
> 📌 **Align your cube face inside the grid. Each cell = one sticker.**
> Hold the cube steady, ensure good lighting, then click **Scan**.
""")

        face_pick = st.selectbox("Which face to capture?", FACE_LABELS,
            format_func=lambda f: f"{f} — {FACE_NAMES[f]}  (center: {FACE_CENTERS[f]})",
            key="cam_face_pick")

        cam_col, right_col = st.columns([1.4, 1])

        with cam_col:
            st.markdown("<div class='sec'>📷 Camera — align cube inside the grid</div>",
                        unsafe_allow_html=True)
            cam_img = st.camera_input(
                f"Face {face_pick} ({FACE_NAMES[face_pick]}) — center must be {FACE_CENTERS[face_pick].upper()}",
                key=f"cam_{face_pick}")

            # Show grid guide image as hint
            import cv2, numpy as np
            guide = np.zeros((300,300,3), dtype=np.uint8)
            guide[:] = (18,18,26)
            sy, sx = 100, 100
            for k in range(1,3):
                cv2.line(guide,(k*sx,0),(k*sx,300),(0,255,180),2)
                cv2.line(guide,(0,k*sy),(300,k*sy),(0,255,180),2)
            cv2.rectangle(guide,(0,0),(299,299),(0,255,180),3)
            # Label cells
            labels = ["TL","TM","TR","ML","CTR","MR","BL","BM","BR"]
            for idx, lbl in enumerate(labels):
                r, c = divmod(idx, 3)
                cx, cy = c*sx + sx//2, r*sy + sy//2
                cv2.putText(guide, lbl, (cx-14, cy+6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,200,150), 1)
            st.image(cv2.cvtColor(guide, cv2.COLOR_BGR2RGB),
                     caption="Grid guide — fill this area with your cube face",
                     use_column_width=True)

        with right_col:
            st.markdown(f"""
**Face {face_pick} — {FACE_NAMES[face_pick]}**
Center sticker must be **{FACE_CENTERS[face_pick].upper()}**

**📸 Tips for best scan:**
- 💡 Good lighting (face a window)
- 📐 Hold cube flat, square to camera
- 🔲 Fill the entire camera frame
- ⏸️ Hold steady before clicking capture
""")
            st.markdown("<div class='sec'>Progress</div>", unsafe_allow_html=True)
            for fl in FACE_LABELS:
                is_set = len(set(st.session_state.faces[fl])) > 1
                active = "→ " if fl == face_pick else "   "
                st.write(f"{active}{'✅' if is_set else '⬜'} {fl} — {FACE_NAMES[fl]}")

        # Scan button + result
        if cam_img:
            img_b64 = base64.b64encode(cam_img.getvalue()).decode()

            # Show captured image with grid overlay immediately
            import cv2, numpy as np
            file_bytes = np.frombuffer(cam_img.getvalue(), np.uint8)
            img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img_cv is not None:
                h, w = img_cv.shape[:2]
                sy2, sx2 = h//3, w//3
                # Thick grid lines
                for k in range(1,3):
                    cv2.line(img_cv,(k*sx2,0),(k*sx2,h),(0,255,180),3)
                    cv2.line(img_cv,(0,k*sy2),(w,k*sy2),(0,255,180),3)
                cv2.rectangle(img_cv,(0,0),(w-1,h-1),(0,255,180),3)
                # Number each cell
                for idx in range(9):
                    r, c = divmod(idx, 3)
                    cx2 = c*sx2 + sx2//2
                    cy2 = r*sy2 + sy2//2
                    cv2.putText(img_cv, str(idx+1), (cx2-8, cy2+8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,180), 2)
                st.image(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB),
                         caption="📷 Captured — grid shows 9 sticker zones (numbered 1–9)",
                         use_column_width=True)

            if st.button(f"🔍 Scan Face {face_pick}", type="primary", use_container_width=True):
                with st.spinner(f"AI scanning face {face_pick}…"):
                    face_idx = FACE_LABELS.index(face_pick)
                    result = api("scan-frame", {"image": img_b64, "draw_overlay": True, "face_index": face_idx})
                    if result:
                        colors = result.get("colors", ["white"]*9)
                        st.session_state.faces[face_pick] = colors
                        st.session_state.cam_edit_face = face_pick

                        if "preview" in result:
                            st.image(base64.b64decode(result["preview"]),
                                     caption="🤖 AI Detection — colored overlay shows detected colors",
                                     use_column_width=True)

                        # Show detected colors as swatches
                        st.markdown("<div class='sec'>Detected colors (stickers 1–9):</div>",
                                    unsafe_allow_html=True)
                        sw_cols = st.columns(9)
                        for idx, col in enumerate(colors):
                            with sw_cols[idx]:
                                st.markdown(
                                    f"<div style='text-align:center;'>"
                                    f"<div style='height:30px;border-radius:5px;"
                                    f"background:{COLOR_HEX[col]};'></div>"
                                    f"<span style='font-size:.6rem;color:#aaa;'>{idx+1}</span>"
                                    f"</div>", unsafe_allow_html=True)

                        st.success(f"✓ Face {face_pick} scanned! Correct below if needed.")
                        st.rerun()

        # ── Manual correction grid for camera ─────────────────────────────────
        st.divider()
        cam_edit_c1, cam_edit_c2 = st.columns([1, 1.2])

        with cam_edit_c1:
            st.markdown("<div class='sec'>All faces so far</div>", unsafe_allow_html=True)
            show_cube_2d(faces_to_list(), "Current Cube State")

        with cam_edit_c2:
            st.markdown("<div class='sec'>Manually correct any face</div>", unsafe_allow_html=True)
            cam_correct_face = st.selectbox(
                "Select face to fix", FACE_LABELS,
                format_func=lambda f: f"{f} — {FACE_NAMES[f]}",
                key="cam_correct_select",
                index=FACE_LABELS.index(face_pick))
            render_correction_grid(cam_correct_face, "cam", "cam_edit_color")

    # ── Action Buttons ─────────────────────────────────────────────────────────
    st.divider()
    b1, b2, b3 = st.columns(3)

    with b1:
        if st.button("▶  Solve", type="primary", use_container_width=True):
            with st.spinner("Computing solution…"):
                result = api("solve", {"cube_faces": faces_to_list()})
                if result:
                    if result.get("success"):
                        st.session_state.solution = result.get("steps", [])
                        st.session_state.step     = 0
                        st.session_state.faces    = list_to_faces(result["faces"])
                        st.success(f"✓ Solution: {len(st.session_state.solution)} moves")
                    else:
                        st.error(result.get("error","Solver error"))
                        st.session_state.solution = []

    with b2:
        if st.button("⚡ Scramble", use_container_width=True):
            with st.spinner("Scrambling…"):
                result = api("scramble", {"moves": 20})
                if result:
                    st.session_state.faces    = list_to_faces(result["cube_faces"])
                    st.session_state.solution = []
                    st.session_state.step     = 0
                    st.info("Scramble: " + " ".join(result["scramble_moves"]))
                    st.rerun()

    with b3:
        if st.button("↺ Reset", use_container_width=True):
            st.session_state.faces    = _default_faces()
            st.session_state.solution = []
            st.session_state.step     = 0
            st.rerun()

    # ── Solution Display ───────────────────────────────────────────────────────
    if st.session_state.solution:
        st.divider()
        st.markdown("### 📋 Solution")
        sol   = st.session_state.solution
        step  = st.session_state.step
        total = len(sol)
        st.progress(step/total if total else 0,
                    text=f"Step {step} / {total}  ({int(step/total*100) if total else 0}%)")
        chips = ""
        for i, m in enumerate(sol):
            css = "done" if i < step else ("current" if i == step else "")
            chips += f"<span class='move-chip {css}'>{m}</span>"
        st.markdown(chips, unsafe_allow_html=True)

        n1,n2,n3,n4,n5 = st.columns(5)
        with n1:
            if st.button("⏮ First"):
                st.session_state.step = 0; st.rerun()
        with n2:
            if st.button("◀ Prev") and step > 0:
                st.session_state.step -= 1; st.rerun()
        with n3:
            st.markdown(f"<div style='text-align:center;padding-top:8px;"
                        f"font-family:monospace;color:#00ffcc;'>{step}/{total}</div>",
                        unsafe_allow_html=True)
        with n4:
            if st.button("Next ▶") and step < total:
                st.session_state.step += 1; st.rerun()
        with n5:
            if st.button("Last ⏭"):
                st.session_state.step = total; st.rerun()

        if step == total > 0:
            st.balloons()
            st.success("🎉 Cube solved!")

    # ── Full Cube View ─────────────────────────────────────────────────────────
    st.divider()
    fl = faces_to_list()
    show_cube_3d(fl,"3D Cube View") if view3d else show_cube_2d(fl,"Full Cube State")

    with st.expander("🔍 Color Validation"):
        from collections import Counter
        counts = Counter(c for face in fl for c in face)
        vcols  = st.columns(6)
        for i, color in enumerate(VALID_COLORS):
            cnt = counts.get(color,0); ok = cnt==9
            with vcols[i]:
                st.markdown(
                    f"<div style='text-align:center;padding:8px;border-radius:8px;"
                    f"background:{COLOR_HEX[color]};border:2px solid {'#00ffcc' if ok else '#e53935'};'>"
                    f"<b style='color:rgba(0,0,0,.65);font-size:.75rem;'>{color[:3].upper()}</b><br>"
                    f"<b style='color:rgba(0,0,0,.7);font-size:1.1rem;'>{cnt}/9</b></div>",
                    unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# ABOUT PAGE
# ═════════════════════════════════════════════════════════════════════════════
elif "About" in page:
    st.markdown("# 🧊 SmartCube AI")
    st.markdown("### AI-Powered Rubik's Cube Solver")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("""
**Tech Stack**
- Python + FastAPI
- Streamlit (this UI)
- OpenCV + CLAHE (vision)
- KMeans + LAB colorspace (color AI)
- TensorFlow CNN (optional)
- Kociemba algorithm (solver ≤20 moves)
- Matplotlib (visualisation)
""")
    with c2:
        st.markdown("""
**How It Works**
1. Input cube via manual / upload / camera
2. OpenCV extracts 9 sticker tiles per face
3. AI predicts color of each sticker
4. Validator checks cube is legal (each color ×9)
5. Kociemba computes optimal solution
6. Step-by-step guide shown in UI

**Author:** Subham Dash — B.Tech CSE, AI & ML
""")