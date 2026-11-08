import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import lutlib as L

ROOT = os.path.join(os.path.dirname(__file__), "..")
base = L.load_png(os.path.join(ROOT, "luts", "classicv12balance.lut.png"))
names = ["sodium_dusk", "cold_flash", "cream_halation"]
luts = {n: L.load_png(os.path.join(ROOT, "custom", f"fb_{n}.lut.png")) for n in names}

# ---- numeric checks ----
for n, lut in luts.items():
    ax = lut[np.arange(64), np.arange(64), np.arange(64)]
    lum = ax @ np.array([0.2126, 0.7152, 0.0722])
    mono = np.all(np.diff(lum) > -1e-3)
    # smoothness: max neighbour step along each axis
    step = max(np.abs(np.diff(lut, axis=i)).max() for i in range(3))
    bstep = max(np.abs(np.diff(base, axis=i)).max() for i in range(3))
    # neutral tint
    tint = lambda i: np.round((ax[i] - ax[i].mean()) * 255, 1)
    print(f"\n{n}: neutral ramp monotonic={mono}  max node step={step*255:.1f}/255 (classic base {bstep*255:.1f})")
    print("  black", np.round(ax[0]*255).astype(int), " shadow(8)", np.round(ax[8]*255).astype(int),
          " mid(32)", np.round(ax[32]*255).astype(int), " high(56)", np.round(ax[56]*255).astype(int),
          " white", np.round(ax[63]*255).astype(int))

# ---- preview image ----
rng = np.random.default_rng(3)
W, H = 360, 520
def make_input():
    img = np.zeros((H, W, 3))
    # hue x lightness grid (top)
    hs = np.linspace(0, 1, 12, endpoint=False)
    import colorsys
    for j in range(5):
        for i, hh in enumerate(hs):
            v = 0.25 + 0.15 * j
            s = 0.75 if j < 4 else 0.35
            c = colorsys.hsv_to_rgb(hh, s, v + 0.1)
            img[j*24:(j+1)*24, i*30:(i+1)*30] = c
    # grey ramp
    ramp = np.linspace(0, 1, W)[None, :, None] * np.ones((28, 1, 3))
    img[124:152] = ramp
    # skin tones
    skins = [(0.95, 0.80, 0.70), (0.85, 0.62, 0.48), (0.66, 0.45, 0.33), (0.45, 0.30, 0.22), (0.32, 0.20, 0.15)]
    for i, s in enumerate(skins):
        img[158:196, i*72:(i+1)*72] = s
    # pseudo scene: sky gradient, foliage, warm window light
    y = np.linspace(0, 1, 140)[:, None]
    sky = np.concatenate([0.25 + 0.5*y, 0.45 + 0.35*y, 0.75 + 0.1*y*0 + 0*y], -1)[:, None, :] * np.ones((1, W, 1))
    img[200:340] = sky[:140]
    xx = np.linspace(0, 1, W)[None, :]
    hill = (0.18 + 0.05*np.sin(xx*9))*140
    for x in range(W):
        top = int(340 - hill[0, x])
        img[top:340, x] = [0.18 + 0.08*rng.random(), 0.32 + 0.1*rng.random(), 0.10]
    img[230:290, 40:110] = [1.0, 0.82, 0.45]; img[232:288, 44:106] = [1.0, 0.93, 0.7]  # lit window
    img[345:520] = img[345:520]  # night block:
    ny = np.linspace(0, 1, 175)[:, None, None]
    night = np.concatenate([0.03 + 0.05*ny, 0.04 + 0.06*ny, 0.10 + 0.12*ny], -1) * np.ones((1, W, 1))
    img[345:520] = night
    for _ in range(14):
        cx, cy = rng.integers(20, W-20), rng.integers(360, 500)
        r = rng.integers(6, 20)
        yy, xxg = np.ogrid[:H, :W]
        m = np.exp(-(((xxg-cx)**2 + (yy-cy)**2) / (2*(r/2)**2)))[..., None]
        col = np.array([[1.0, 0.7, 0.3], [0.9, 0.3, 0.4], [0.3, 0.8, 1.0], [1, 1, 0.9]][rng.integers(0, 4)])
        img = np.clip(img + m * col * 0.9, 0, 1)
    return img

inp = make_input()
cls = L.apply(base, inp)
panels = [("Classic v12 (base)", cls)] + [(n.replace('_', ' ').title(), L.apply(l, inp)) for n, l in luts.items()]
sheet = Image.new("RGB", (W * 4 + 30, H + 24), (18, 18, 18))
d = ImageDraw.Draw(sheet)
for i, (t, im) in enumerate(panels):
    sheet.paste(Image.fromarray(np.round(np.clip(im, 0, 1) * 255).astype(np.uint8)), (i * (W + 10), 24))
    d.text((i * (W + 10) + 4, 6), t, fill=(230, 230, 230))
out = os.path.join(ROOT, "custom", "preview_synthetic.png")
sheet.save(out)
print("\npreview:", out)

# clipping / gamut stats on a test set
for n, l in luts.items():
    o = L.apply(l, inp)
    print(n, "pixels at 0: %.2f%%, at 1: %.2f%%" % (100*np.mean(o.min(-1) <= 0.002), 100*np.mean(o.max(-1) >= 0.998)))
