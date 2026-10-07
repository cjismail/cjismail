"""ParaView-style cube thumbnails of the sine.m / write_vtk.m composition fields.

sine.m builds a Nx*Ny*Nz volume that only varies along y:
    c(y) = avg + amp*sin(2*pi*y/wv),  last y layer = avg   (the "PBC" line)
In ParaView only the outer surface of that volume is visible, so the cube is drawn
straight from the 1-D profile instead of from a 1280^3 array:
  * left / right faces -> colour along the vertical edge follows c(y)
  * top face           -> flat colour of the last y layer
  * colour range       -> auto-scaled to [min(c), max(c)] (ParaView default)
  * colour map         -> "Cool to Warm" (Moreland diverging, = matplotlib coolwarm)
Camera, background and per-face shading were measured from the ParaView
screenshots in VTK_Field_Report.xlsx (mean abs. error vs those 20 images ~1.6/255).
"""
import numpy as np
from PIL import Image
from matplotlib import colormaps

CMAP = colormaps["coolwarm"]
BG = np.array([98, 93, 90], float)      # ParaView screenshot background
SIZE = 318                              # thumbnail size in the report

# Cube corners (pixels) in the 318x318 ParaView view; the view is mirror-symmetric.
CORNERS = dict(
    apex=(158.5, 49.0), ftop=(158.5, 104.0), fbot=(158.5, 306.6),
    ltop=(27.0, 72.0), lbot=(40.0, 238.3),
    rtop=(290.0, 72.0), rbot=(277.0, 238.3),
)
# Per-face brightness (fit to the screenshots).  The top face also sits ~0.03 higher on
# the colour map than the raw value; that offset is empirical (ParaView texture lookup).
K_TOP, K_LEFT, K_RIGHT = 0.7575, 0.48, 0.575
TOP_T_OFFSET = 0.03


def _homography(src, dst):
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    return np.linalg.svd(np.array(rows, float))[2][-1].reshape(3, 3)


def _apply(H, X, Y):
    q = H @ np.stack([X.ravel(), Y.ravel(), np.ones(X.size)])
    return (q[0] / q[2]).reshape(X.shape), (q[1] / q[2]).reshape(X.shape)


def render(c, ss=3):
    """c: 1-D field along y, bottom -> top (top entry = last y layer). Returns uint8 RGB."""
    c = np.asarray(c, float)
    lo, hi = c.min(), c.max()
    span = (hi - lo) or 1.0
    p = CORNERS
    n = SIZE * ss
    xs = (np.arange(n) + 0.5) / ss
    X, Y = np.meshgrid(xs, xs)
    img = np.tile(BG, (n, n, 1))

    def colour(vals, offset=0.0):
        t = np.clip((vals - lo) / span + offset, 0, 1)
        return CMAP(t)[..., :3] * 255

    unit = [(0, 1), (1, 1), (1, 0), (0, 0)]     # (u across, v up the face)
    for quad, k in (((p["ltop"], p["ftop"], p["fbot"], p["lbot"]), K_LEFT),
                    ((p["ftop"], p["rtop"], p["rbot"], p["fbot"]), K_RIGHT)):
        u, v = _apply(_homography(quad, unit), X, Y)
        inside = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
        val = np.interp(np.clip(v, 0, 1) * (len(c) - 1), np.arange(len(c)), c)
        img[inside] = (colour(val) * k)[inside]

    top = (p["apex"], p["rtop"], p["ftop"], p["ltop"])
    cross = np.stack([(top[(i + 1) % 4][0] - top[i][0]) * (Y - top[i][1])
                      - (top[(i + 1) % 4][1] - top[i][1]) * (X - top[i][0]) for i in range(4)])
    in_top = np.all(cross >= 0, 0) | np.all(cross <= 0, 0)
    img[in_top] = colour(np.array([c[-1]]), TOP_T_OFFSET)[0] * K_TOP

    img = np.clip(img, 0, 255).reshape(SIZE, ss, SIZE, ss, 3).mean((1, 3))
    return np.round(img).astype(np.uint8)


def sine_profile(avg, wv, amp, L=640.0, n=640):
    """Field of sine.m along y over a domain of length L (same units as wv)."""
    y = np.arange(n) * (L / n)
    c = avg + amp * np.sin(2 * np.pi * y / wv)
    c[-1] = avg
    return c


def save_png(c, path):
    Image.fromarray(render(c)).save(path, optimize=True)
