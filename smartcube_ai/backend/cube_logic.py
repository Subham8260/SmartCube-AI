"""
cube_logic.py — SmartCube AI
Full 3×3 Rubik's Cube move logic.

The cube state is represented as a dict:
    { "U": [c0..c8], "R": [...], "F": [...], "D": [...], "L": [...], "B": [...] }

Each face list has 9 elements in reading order (row-major, top-left → bottom-right):
    0 1 2
    3 4 5
    6 7 8

Supported moves: F R U B L D  (clockwise)
                 F' R' U' B' L' D'  (counter-clockwise)
                 F2 R2 U2 B2 L2 D2  (180°)
"""

import copy
from typing import Union

# ---------------------------------------------------------------------------
# Face rotation helpers
# ---------------------------------------------------------------------------

def _rotate_face_cw(face: list) -> list:
    """Rotate a face 90° clockwise."""
    return [face[6], face[3], face[0],
            face[7], face[4], face[1],
            face[8], face[5], face[2]]


def _rotate_face_ccw(face: list) -> list:
    """Rotate a face 90° counter-clockwise."""
    return [face[2], face[5], face[8],
            face[1], face[4], face[7],
            face[0], face[3], face[6]]


def _rotate_face_180(face: list) -> list:
    """Rotate a face 180°."""
    return list(reversed(face))


# ---------------------------------------------------------------------------
# Single-move application
# ---------------------------------------------------------------------------

# Each entry maps move-name → (face-to-rotate, rotation, cycle-of-sticker-indices)
# The cycle is a list of (face, [i0, i1, i2]) tuples in CW order.
_MOVE_TABLE = {
    "U": ("U", "cw",  [("B", [0,1,2]), ("R", [0,1,2]), ("F", [0,1,2]), ("L", [0,1,2])]),
    "D": ("D", "cw",  [("F", [6,7,8]), ("R", [6,7,8]), ("B", [6,7,8]), ("L", [6,7,8])]),
    "R": ("R", "cw",  [("U", [2,5,8]), ("B", [6,3,0]), ("D", [2,5,8]), ("F", [2,5,8])]),
    "L": ("L", "cw",  [("U", [0,3,6]), ("F", [0,3,6]), ("D", [0,3,6]), ("B", [8,5,2])]),
    "F": ("F", "cw",  [("U", [6,7,8]), ("R", [0,3,6]), ("D", [2,1,0]), ("L", [8,5,2])]),
    "B": ("B", "cw",  [("U", [2,1,0]), ("L", [0,3,6]), ("D", [6,7,8]), ("R", [8,5,2])]),
}


def apply_move(state: dict, move: str) -> dict:
    """
    Return a NEW cube state after applying *move*.
    The original state is not mutated.

    Parameters
    ----------
    state : dict  { face: [9 colors] }
    move  : str   e.g. "R", "U'", "F2"
    """
    move = move.strip()
    if not move:
        return state

    # Parse move
    base = move[0].upper()
    suffix = move[1:] if len(move) > 1 else ""

    if base not in _MOVE_TABLE:
        raise ValueError(f"Unknown move: {move!r}")

    face_key, _, cycle = _MOVE_TABLE[base]

    new = copy.deepcopy(state)

    if suffix == "2":
        new = _apply_single(new, base, cycle, face_key)
        new = _apply_single(new, base, cycle, face_key)
    elif suffix in ("'", "`", "i", "I"):
        # CCW = 3 × CW
        for _ in range(3):
            new = _apply_single(new, base, cycle, face_key)
    else:
        new = _apply_single(new, base, cycle, face_key)

    return new


def _apply_single(state: dict, base: str, cycle: list, face_key: str) -> dict:
    """Apply one 90° CW turn of *base*."""
    new = copy.deepcopy(state)

    # Rotate the face itself
    new[face_key] = _rotate_face_cw(state[face_key])

    # Cycle the adjacent sticker strips
    # cycle = [(face, [i0,i1,i2]), ...] in CW order
    # CW turn: last strip's values go to first strip's positions
    saved = [state[cycle[-1][0]][i] for i in cycle[-1][1]]

    for k in range(len(cycle) - 1, 0, -1):
        src_face, src_idx = cycle[k - 1]
        dst_face, dst_idx = cycle[k]
        for j in range(3):
            new[dst_face][dst_idx[j]] = state[src_face][src_idx[j]]

    dst_face, dst_idx = cycle[0]
    for j in range(3):
        new[dst_face][dst_idx[j]] = saved[j]

    return new


# ---------------------------------------------------------------------------
# Apply a sequence of moves
# ---------------------------------------------------------------------------

def apply_moves(state: dict, moves: Union[list, str]) -> dict:
    """
    Apply a list (or space-separated string) of moves to *state*.
    Returns the final state.
    """
    if isinstance(moves, str):
        moves = moves.split()
    for m in moves:
        state = apply_move(state, m)
    return state


# ---------------------------------------------------------------------------
# Solved-state factory & checker
# ---------------------------------------------------------------------------

FACE_CENTER_COLOR = {
    "U": "white",
    "R": "red",
    "F": "blue",
    "D": "yellow",
    "L": "orange",
    "B": "green",
}

def solved_state() -> dict:
    """Return a pristine solved cube state."""
    return {face: [color] * 9 for face, color in FACE_CENTER_COLOR.items()}


def is_solved(state: dict) -> bool:
    """Return True iff every face is a single color."""
    return all(len(set(tiles)) == 1 for tiles in state.values())


# ---------------------------------------------------------------------------
# Scramble helper
# ---------------------------------------------------------------------------

import random

_ALL_MOVES = ["F","R","U","B","L","D","F'","R'","U'","B'","L'","D'","F2","R2","U2","B2","L2","D2"]

def scramble(n: int = 20, seed: int = None) -> tuple[dict, list]:
    """
    Return (scrambled_state, move_list) after *n* random moves.
    Consecutive moves on the same face are avoided.
    """
    if seed is not None:
        random.seed(seed)

    state = solved_state()
    moves = []
    last_base = ""

    while len(moves) < n:
        m = random.choice(_ALL_MOVES)
        if m[0] == last_base:
            continue
        state = apply_move(state, m)
        moves.append(m)
        last_base = m[0]

    return state, moves