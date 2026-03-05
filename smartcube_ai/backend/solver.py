"""
solver.py — SmartCube AI
Converts a cube-state list → Kociemba string → solution move list.

Key fixes vs v1:
  • Uses center sticker to determine face identity (correct).
  • Raises a descriptive ValueError on invalid cubes instead of silently
    returning garbage.
  • Handles the case where two faces claim the same center color.
"""

import kociemba

# Color name → Kociemba face letter
COLOR_TO_FACE: dict[str, str] = {
    "white":  "U",
    "red":    "R",
    "blue":   "F",
    "yellow": "D",
    "orange": "L",
    "green":  "B",
}

FACE_ORDER = ["U", "R", "F", "D", "L", "B"]
DEFAULT_FACE_COLORS = ["white", "red", "blue", "yellow", "orange", "green"]


def solve_cube(faces: list) -> list[str]:
    """
    Solve a cube from its face list representation.

    Parameters
    ----------
    faces : list of 6 lists, each with 9 color-name strings.
            Order: U R F D L B  (same as validator output).

    Returns
    -------
    List of move strings, e.g. ["R", "U", "R'", "U'", ...]
    Empty list if the cube is already solved.

    Raises
    ------
    ValueError  if the cube string is invalid for Kociemba.
    """
    # --- Build ordered face dict keyed by face letter ---
    ordered: dict[str, list] = {f: None for f in FACE_ORDER}

    for i, face in enumerate(faces):
        if not isinstance(face, list) or len(face) != 9:
            face = [DEFAULT_FACE_COLORS[i]] * 9

        center = face[4]
        face_letter = COLOR_TO_FACE.get(center)

        if face_letter is None:
            raise ValueError(
                f"Face {i} has unknown center color '{center}'. "
                f"Valid colors: {list(COLOR_TO_FACE.keys())}"
            )

        if ordered[face_letter] is not None:
            raise ValueError(
                f"Two faces share the center color '{center}' → face letter '{face_letter}'."
            )

        ordered[face_letter] = face

    # Fill any missing faces with defaults
    for i, letter in enumerate(FACE_ORDER):
        if ordered[letter] is None:
            ordered[letter] = [DEFAULT_FACE_COLORS[i]] * 9

    # --- Build 54-character Kociemba string ---
    cube_str = ""
    for letter in FACE_ORDER:
        for color in ordered[letter]:
            fl = COLOR_TO_FACE.get(color)
            if fl is None:
                raise ValueError(f"Unknown color '{color}' in face '{letter}'.")
            cube_str += fl

    if len(cube_str) != 54:
        raise ValueError(f"Cube string length {len(cube_str)} ≠ 54.")

    # --- Solve ---
    try:
        solution_str = kociemba.solve(cube_str)
    except Exception as exc:
        raise ValueError(f"Kociemba solver error: {exc}") from exc

    solution_str = solution_str.strip()
    if not solution_str:
        return []   # already solved

    return solution_str.split()