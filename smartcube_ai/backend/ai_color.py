import numpy as np
from sklearn.cluster import KMeans

COLOR_MAP = {
    "white": np.array([255, 255, 255]),
    "red": np.array([255, 0, 0]),
    "blue": np.array([0, 0, 255]),
    "yellow": np.array([255, 255, 0]),
    "orange": np.array([255, 165, 0]),
    "green": np.array([0, 128, 0]),
}

def closest_color(rgb):
    best, dist = "white", float("inf")
    for name, value in COLOR_MAP.items():
        d = np.linalg.norm(rgb - value)
        if d < dist:
            best, dist = name, d
    return best

def predict_colors(tiles):
    colors = []
    for img in tiles:
        pixels = img.reshape((-1, 3))
        model = KMeans(n_clusters=1, n_init=5)
        model.fit(pixels)
        dominant = model.cluster_centers_[0]
        colors.append(closest_color(dominant))
    return colors
