import cv2

def extract_tiles(frame):
    frame = cv2.resize(frame, (300, 300))
    tiles = []
    size = 100

    for y in range(0, 300, size):
        for x in range(0, 300, size):
            tiles.append(frame[y:y+size, x:x+size])

    return tiles
