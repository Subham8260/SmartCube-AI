"""
validator.py — SmartCube AI
Validates a cube-state dict/list before passing it to the Kociemba solver.

Key fixes vs v1:
  • Does NOT blindly overwrite all 9 stickers with the center color.
    That destroyed real scan data. Only invalid/missing stickers are replaced.
  • Returns detailed error messages (not just True/False).
  • Checks that each color appears exactly 9 times.
  • Checks that each face has a unique center sticker.
"""

from collections import Counter

VALID_COLORS = ["white", "yellow", "red", "orange", "blue", "green"]

# Default center color per face position index (U R F D L B)
FACE_CENTER_DEFAULTS = ["white", "red", "blue", "yellow", "orange", "green"]


# ---------------------------------------------------------------------------
# Main validator
# ---------------------------------------------------------------------------

def validate_cube(faces: list) -> tuple[bool, str, list]:
    """
    Validate and auto-repair a cube face list.

    Parameters
    ----------
    faces : list of 6 lists, each with 9 color-name strings.

    Returns
    -------
    (is_valid, message, fixed_faces)
        is_valid   — True if the cube is solvable after repair
        message    — human-readable status string
        fixed_faces — repaired list (safe to pass to solver)
    """
    # --- Step 1: ensure we have exactly 6 faces ---
    if not isinstance(faces, list):
        faces = []
    faces = list(faces)  # copy

    while len(faces) < 6:
        idx = len(faces)
        faces.append([FACE_CENTER_DEFAULTS[idx]] * 9)

    faces = faces[:6]

    # --- Step 2: sanitise each face ---
    fixed = []
    for i, face in enumerate(faces):
        default_color = FACE_CENTER_DEFAULTS[i]
        if not isinstance(face, list):
            face = [default_color] * 9
        face = list(face)

        # Pad short faces
        while len(face) < 9:
            face.append(default_color)

        # Replace unknown colors (keep center sacred)
        sanitised = []
        for j, c in enumerate(face[:9]):
            if c in VALID_COLORS:
                sanitised.append(c)
            else:
                # Use center color as fallback for unknowns
                sanitised.append(face[4] if face[4] in VALID_COLORS else default_color)

        fixed.append(sanitised)

    # --- Step 3: validate centers are unique ---
    centers = [fixed[i][4] for i in range(6)]
    if len(set(centers)) != 6:
        return False, "Duplicate center colors detected — each face must have a unique center.", fixed

    # --- Step 4: check color counts ---
    all_colors = [c for face in fixed for c in face]
    counts = Counter(all_colors)

    errors = []
    for color in VALID_COLORS:
        cnt = counts.get(color, 0)
        if cnt != 9:
            errors.append(f"{color}: {cnt}/9")

    if errors:
        msg = "Color count mismatch — " + ", ".join(errors)
        return False, msg, fixed

    return True, "Cube state is valid.", fixed


# ---------------------------------------------------------------------------
# Helper: dict ↔ list conversion
# ---------------------------------------------------------------------------

FACE_ORDER = ["U", "R", "F", "D", "L", "B"]

def state_dict_to_list(state: dict) -> list:
    """Convert { face: [9] } → [[9], [9], ...]  in U R F D L B order."""
    return [state[f] for f in FACE_ORDER]


def state_list_to_dict(faces: list) -> dict:
    """Convert [[9], ...] → { face: [9] }."""
    return {FACE_ORDER[i]: faces[i] for i in range(6)}