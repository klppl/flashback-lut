"""Flashback LUT helpers.

App format: 512x512 PNG, 64^3 CLUT in 8x8 tiles.
  pixel x = (b % 8) * 64 + r ; pixel y = (b // 8) * 64 + g
Returned arrays are float [b, g, r, 3] in 0..1 so lut[b,g,r] = output RGB.
"""
import numpy as np
from PIL import Image

N = 64
T = 8


def load_png(path):
    im = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
    lut = np.zeros((N, N, N, 3))
    for b in range(N):
        ty, tx = divmod(b, T)
        lut[b] = im[ty * N:(ty + 1) * N, tx * N:(tx + 1) * N]  # [g, r]
    return lut


def save_png(lut, path):
    lut = np.clip(lut, 0, 1)
    im = np.zeros((512, 512, 3))
    for b in range(N):
        ty, tx = divmod(b, T)
        im[ty * N:(ty + 1) * N, tx * N:(tx + 1) * N] = lut[b]
    Image.fromarray(np.round(im * 255).astype(np.uint8), "RGB").save(path, optimize=True)


def identity():
    g = np.linspace(0, 1, N)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    return np.stack([r, gg, b], axis=-1)


def save_cube(lut, path, title, size=N):
    """.cube: red varies fastest, then green, then blue."""
    lut = np.clip(lut, 0, 1)
    with open(path, "w") as f:
        f.write(f'TITLE "{title}"\nLUT_3D_SIZE {size}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        for b in range(size):
            for g in range(size):
                for r in range(size):
                    v = lut[b, g, r]
                    f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")


def apply(lut, img):
    """Trilinear apply to float image HxWx3 (0..1)."""
    x = np.clip(img, 0, 1) * (N - 1)
    i0 = np.floor(x).astype(int)
    i1 = np.minimum(i0 + 1, N - 1)
    f = x - i0
    out = 0
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                ir = (i1 if dr else i0)[..., 0]
                ig = (i1 if dg else i0)[..., 1]
                ib = (i1 if db else i0)[..., 2]
                w = ((f[..., 0] if dr else 1 - f[..., 0])
                     * (f[..., 1] if dg else 1 - f[..., 1])
                     * (f[..., 2] if db else 1 - f[..., 2]))
                out = out + w[..., None] * lut[ib, ig, ir]
    return out


# ---- OKLab -----------------------------------------------------------------
def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])


def srgb_to_oklab(c):
    lin = srgb_to_lin(c)
    lms = np.cbrt(lin @ _M1.T)
    return lms @ _M2.T


def oklab_to_srgb(lab):
    lms = lab @ np.linalg.inv(_M2).T
    lin = (lms ** 3) @ np.linalg.inv(_M1).T
    return lin_to_srgb(lin), lin
