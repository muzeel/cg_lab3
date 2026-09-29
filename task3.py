import numpy as np
import matplotlib.pyplot as plt


def rasterize_triangle(p0, p1, p2, c0, c1, c2, width, height):
    """
    Растеризует треугольник с градиентной заливкой.
    p0,p1,p2 — координаты вершин (x, y) в экранных пикселях
    c0,c1,c2 — цвета вершин (r, g, b), 0..255
    """
    img = np.zeros((height, width, 3), dtype=np.uint8)

    denom = ((p1[1] - p2[1]) * (p0[0] - p2[0])
             + (p2[0] - p1[0]) * (p0[1] - p2[1]))
    if abs(denom) < 1e-9:
        return img 

    xs = [p0[0], p1[0], p2[0]]
    ys = [p0[1], p1[1], p2[1]]
    minx = max(0, int(np.floor(min(xs))))
    maxx = min(width  - 1, int(np.ceil(max(xs))))
    miny = max(0, int(np.floor(min(ys))))
    maxy = min(height - 1, int(np.ceil(max(ys))))

    Y, X = np.mgrid[miny:maxy + 1, minx:maxx + 1]
    Xf = X + 0.5
    Yf = Y + 0.5

    w0 = ((p1[1] - p2[1]) * (Xf - p2[0])
          + (p2[0] - p1[0]) * (Yf - p2[1])) / denom
    w1 = ((p2[1] - p0[1]) * (Xf - p2[0])
          + (p0[0] - p2[0]) * (Yf - p2[1])) / denom
    w2 = 1.0 - w0 - w1

    inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
    if not np.any(inside):
        return img

    c0 = np.array(c0, dtype=np.float64)
    c1 = np.array(c1, dtype=np.float64)
    c2 = np.array(c2, dtype=np.float64)

    R = w0 * c0[0] + w1 * c1[0] + w2 * c2[0]
    G = w0 * c0[1] + w1 * c1[1] + w2 * c2[1]
    B = w0 * c0[2] + w1 * c1[2] + w2 * c2[2]

    h_box, w_box = R.shape
    colors = np.zeros((h_box, w_box, 3), dtype=np.uint8)
    for i in range(h_box):
        for j in range(w_box):
            colors[i, j, 0] = np.clip(R[i, j], 0, 255)
            colors[i, j, 1] = np.clip(G[i, j], 0, 255)
            colors[i, j, 2] = np.clip(B[i, j], 0, 255)

    sub = img[miny:maxy + 1, minx:maxx + 1]
    sub[inside] = colors[inside]
    return img

if __name__ == "__main__":
    W, H = 600, 400

    p0 = (100.0, 60.0)
    p1 = (520.0, 140.0)
    p2 = (280.0, 360.0)

    c0 = (255,   0,   0)   
    c1 = (  0, 255,   0)   
    c2 = (  0,   0, 255) 

    img = rasterize_triangle(p0, p1, p2, c0, c1, c2, W, H)

    plt.figure(figsize=(9, 6))
    plt.imshow(img)
    plt.title("Градиентная растеризация треугольника (барицентрическая интерполяция)")
    plt.axis("off")
    plt.tight_layout()
    plt.show()