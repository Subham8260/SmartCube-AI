"""
cube_visual.py — SmartCube AI
Visualization helpers for the Rubik's Cube state.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

HEX_COLORS = {
    "white":  "#f5f5f0",
    "yellow": "#ffd600",
    "red":    "#e53935",
    "orange": "#fb8c00",
    "blue":   "#1e88e5",
    "green":  "#43a047",
}

def _hex(color):
    return HEX_COLORS.get(color, "#888888")


def draw_cube_2d(cube_faces, title="Cube State"):
    layout = {"U":(1,0),"L":(0,1),"F":(1,1),"R":(2,1),"B":(3,1),"D":(1,2)}
    face_names = ["U","R","F","D","L","B"]
    face_dict  = {face_names[i]: cube_faces[i] for i in range(min(6,len(cube_faces)))}

    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_xlim(0,12); ax.set_ylim(0,9)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_facecolor("#111118"); fig.patch.set_facecolor("#111118")
    ax.set_title(title, color="white", fontsize=13, pad=10)
    gap = 0.08

    for face_label,(col_off,row_off) in layout.items():
        face   = face_dict.get(face_label, ["white"]*9)
        x_base = col_off*3
        y_base = (2-row_off)*3
        for idx in range(9):
            r,c = divmod(idx,3)
            x = x_base+c+gap; y = y_base+(2-r)+gap; w = 1-2*gap
            rect = patches.FancyBboxPatch((x,y),w,w,
                boxstyle="round,pad=0.04",linewidth=1,
                edgecolor="#222230",facecolor=_hex(face[idx]))
            ax.add_patch(rect)
        ax.text(x_base+1.5, y_base+1.5, face_label,
                ha="center",va="center",fontsize=9,
                color="#00000066",fontweight="bold",zorder=5)
    plt.tight_layout()
    return fig


def draw_cube_3d(cube_faces, title="3D Cube View", elev=25, azim=40):
    from mpl_toolkits.mplot3d import Axes3D
    face_names = ["U","R","F","D","L","B"]
    face_dict  = {face_names[i]: cube_faces[i] for i in range(min(6,len(cube_faces)))}

    fig = plt.figure(figsize=(7,7))
    ax  = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#111118"); fig.patch.set_facecolor("#111118")
    ax.set_title(title, color="white", fontsize=13, pad=6)
    ax.axis("off")

    def _stickers(fl, face):
        out=[]; sz=0.85/3
        for idx in range(9):
            r,c=divmod(idx,3); col=_hex(face[idx])
            if fl=="U":  out.append((c/3,r/3,1,  sz,sz,  0.01,col))
            elif fl=="D":out.append((c/3,r/3,0,  sz,sz,  0.01,col))
            elif fl=="F":out.append((c/3,1,  r/3,sz,0.01,sz,  col))
            elif fl=="B":out.append((c/3,0,  r/3,sz,0.01,sz,  col))
            elif fl=="R":out.append((1,  c/3,r/3,0.01,sz,sz,  col))
            elif fl=="L":out.append((0,  c/3,r/3,0.01,sz,sz,  col))
        return out

    for fl,face in face_dict.items():
        for (x,y,z,dx,dy,dz,col) in _stickers(fl,face):
            ax.bar3d(x,y,z,dx,dy,dz,color=col,edgecolor="#222230",linewidth=0.5,shade=True)

    ax.view_init(elev=elev,azim=azim)
    ax.set_xlim(0,1.2); ax.set_ylim(0,1.2); ax.set_zlim(0,1.2)
    plt.tight_layout()
    return fig


def show_cube_2d(cube_faces, title="Cube State"):
    try:
        import streamlit as st
        fig = draw_cube_2d(cube_faces, title)
        st.pyplot(fig)
        plt.close(fig)
    except ImportError:
        pass


def show_cube_3d(cube_faces, title="3D Cube View"):
    try:
        import streamlit as st
        fig = draw_cube_3d(cube_faces, title)
        st.pyplot(fig)
        plt.close(fig)
    except ImportError:
        pass


_SYM = {"white":"W","yellow":"Y","red":"R","orange":"O","blue":"B","green":"G"}

def cube_to_ascii(cube_faces):
    fn = ["U","R","F","D","L","B"]
    fd = {fn[i]: cube_faces[i] for i in range(min(6,len(cube_faces)))}
    def _row(f,r):
        return " ".join(_SYM.get(fd[f][r*3+c],"?") for c in range(3))
    lines=[]
    for r in range(3): lines.append("      "+_row("U",r))
    for r in range(3): lines.append(_row("L",r)+"  "+_row("F",r)+"  "+_row("R",r)+"  "+_row("B",r))
    for r in range(3): lines.append("      "+_row("D",r))
    return "\n".join(lines)