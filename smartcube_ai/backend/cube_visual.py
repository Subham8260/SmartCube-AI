import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import streamlit as st

FACE_POSITIONS = {
    "U": (0, 0, 1),
    "R": (1, 0, 0),
    "F": (0, 1, 0),
    "D": (0, 0, -1),
    "L": (-1, 0, 0),
    "B": (0, -1, 0)
}

def draw_cube(cube_faces):
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, projection='3d')

    face_colors = {
        "white":"#ffffff",
        "red":"#ff0000",
        "blue":"#0000ff",
        "yellow":"#ffff00",
        "orange":"#ffa500",
        "green":"#008000"
    }

    face_labels = ["U","R","F","D","L","B"]
    cube_dict = {face_labels[i]: cube_faces[i] for i in range(6)}

    for face_label, face in cube_dict.items():
        for y in range(3):
            for x in range(3):
                color = face_colors.get(face[y*3 + x], "grey")
                ax.bar3d(x + FACE_POSITIONS[face_label][0]*3,
                        y + FACE_POSITIONS[face_label][1]*3,
                        FACE_POSITIONS[face_label][2]*3,
                        1, 1, 0.1,
                        color=color, edgecolor="black")

    ax.view_init(30, 30)
    ax.set_axis_off()
    st.pyplot(fig)
