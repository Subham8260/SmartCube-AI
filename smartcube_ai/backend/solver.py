import kociemba

def solve_cube(cube_faces):
    color_to_face = {
        "white": "U",
        "red": "R",
        "blue": "F",
        "yellow": "D",
        "orange": "L",
        "green": "B"
    }

    ordered_faces = {
        "U": None,
        "R": None,
        "F": None,
        "D": None,
        "L": None,
        "B": None
    }

    for i, face in enumerate(cube_faces):
        if not isinstance(face, list) or len(face) != 9:
            face = ["white"] * 9
        center = face[4] if face[4] in color_to_face else list(color_to_face.keys())[i]
        face_key = color_to_face[center]
        ordered_faces[face_key] = face

    for i, key in enumerate(["U","R","F","D","L","B"]):
        if ordered_faces[key] is None:
            ordered_faces[key] = [list(color_to_face.keys())[i]] * 9

    cube_string = ""
    for key in ["U", "R", "F", "D", "L", "B"]:
        face = ordered_faces[key]
        for color in face:
            cube_string += color_to_face[color]

    return kociemba.solve(cube_string).split()
