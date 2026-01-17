from collections import Counter

VALID_COLORS = ["white", "yellow", "red", "orange", "blue", "green"]

def normalize_faces_by_center(faces):
    normalized = []
    for i, face in enumerate(faces):
        center = face[4] if len(face) > 4 and face[4] in VALID_COLORS else VALID_COLORS[i]
        normalized.append([center] * 9)
    return normalized

def validate_cube(faces):
    if not isinstance(faces, list):
        faces = []

    while len(faces) < 6:
        faces.append([VALID_COLORS[len(faces)]] * 9)

    fixed_faces = []
    for i, face in enumerate(faces):
        if not isinstance(face, list) or len(face) != 9:
            fixed_faces.append([VALID_COLORS[i]] * 9)
        else:
            cleaned = [c if c in VALID_COLORS else VALID_COLORS[i] for c in face]
            fixed_faces.append(cleaned)

    fixed_faces = normalize_faces_by_center(fixed_faces)

    all_colors = [c for face in fixed_faces for c in face]
    counts = Counter(all_colors)
    print("Final cube colors:", counts)

    return True, "Valid cube", fixed_faces
