"""Build the 'Night Shift' LUT family for the Flashback ONE35 V2.

Each look = grade( Classic v12 LUT ).  Building on the camera's own Classic LUT keeps
the app's exposure/encoding assumptions intact; the grade only works on display-ready
colour in OKLab/OKLCH, with a chroma-reducing gamut mapper (no hard clipping).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import lutlib as L

ROOT = os.path.join(os.path.dirname(__file__), "..")
BASE = os.path.join(ROOT, "luts", "classicv12balance.lut.png")
OUT = os.path.join(ROOT, "custom")

D2R = np.pi / 180


def gauss_h(h, center, width):
    d = (h - center * D2R + np.pi) % (2 * np.pi) - np.pi
    return np.exp(-0.5 * (d / (width * D2R)) ** 2)


def smoother(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (x * 6 - 15) + 10)


LOOKS = {
    # name: parameters
    "sodium_dusk": dict(
        title="Sodium Dusk",
        lift=0.05, contrast=0.55, pivot=0.62, white=0.995, knee=0.80, sat=1.05,
        shadow=(-0.011, -0.010), shadow_amt=1.0,      # teal shadows
        high=(0.006, 0.030), high_amt=1.0,            # amber highlights
        mid=(0.0, 0.0),
        hue_gain=[(55, 30, 0.10), (110, 25, 0.06), (195, 30, 0.10), (264, 30, 0.12)],
        hue_rot=[(142, 30, -9), (264, 30, -8)],       # greens -> yellow-olive, blues -> cyan
        skin=0.75,
    ),
    "cold_flash": dict(
        title="Cold Flash",
        lift=0.07, contrast=0.70, pivot=0.62, white=0.995, knee=0.78, sat=1.08,
        shadow=(-0.010, -0.030), shadow_amt=1.0,      # blue-cyan shadows
        high=(0.020, 0.010), high_amt=1.0,            # pink-peach highlights
        mid=(0.004, -0.004),
        hue_gain=[(328, 30, 0.16), (29, 25, 0.06), (195, 30, 0.08)],
        hue_rot=[(142, 30, -14), (110, 20, -5)],
        skin=0.85,
    ),
    "cream_halation": dict(
        title="Cream Halation",
        lift=0.10, contrast=0.20, pivot=0.62, white=0.992, knee=0.76, sat=0.90,
        shadow=(0.004, 0.008), shadow_amt=1.0,        # warm brown shadows
        high=(0.003, 0.024), high_amt=1.0,            # cream highlights
        mid=(0.0, 0.004),
        hue_gain=[(29, 22, 0.20), (55, 25, 0.12), (142, 35, -0.18), (264, 35, -0.10)],
        hue_rot=[(29, 20, 6)],                        # reds glow toward orange
        skin=0.5,
    ),
}


def tone(L0, P):
    """Toe lift (blacks only) + S-curve pivoting at P['pivot'] + soft highlight shoulder."""
    L1 = L0 + P["lift"] * (1 - L0) ** 3
    p, k = P["pivot"], P["contrast"]
    L2 = L1 + k * 3 * L1 * (1 - L1) * (L1 - p)
    knee, wh = P["knee"], P["white"]
    t = np.clip((L2 - knee) / (1 - knee), 0, None)
    rho = max(0.5, (wh - knee) / (1 - knee))
    shoulder = knee + (1 - knee) * (t - (1 - rho) * t * t)
    return np.where(L2 > knee, shoulder, L2)


def grade(rgb, P):
    lab = L.srgb_to_oklab(rgb)
    L0, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    h = np.arctan2(b, a)

    L1 = np.clip(tone(L0, P), 0, 1)

    gain = np.ones_like(h)
    for c, w, g in P["hue_gain"]:
        gain = gain + g * gauss_h(h, c, w)
    fade = 1 - smoother((C - 0.14) / 0.16)   # leave already-vivid colours alone (avoids gamut ridges)
    C1 = C * (1 + (P["sat"] * gain - 1) * fade)
    # protect near-neutral from hue-gain noise, ease sat into highlights
    C1 = C1 * (1 - 0.35 * smoother((L1 - 0.88) / 0.12))

    h1 = h.copy()
    for c, w, deg in P["hue_rot"]:
        h1 = h1 + deg * D2R * gauss_h(h, c, w) * smoother(C / 0.06) * fade

    a1, b1 = C1 * np.cos(h1), C1 * np.sin(h1)

    ws = (1 - L1) ** 2.4
    wh = L1 ** 2.6
    wm = 4 * L1 * (1 - L1)
    skin = 1 - P["skin"] * gauss_h(h, 55, 22) * smoother(C / 0.05)
    a1 = a1 + skin * (P["shadow"][0] * ws * P["shadow_amt"] + P["high"][0] * wh * P["high_amt"] + P["mid"][0] * wm)
    b1 = b1 + skin * (P["shadow"][1] * ws * P["shadow_amt"] + P["high"][1] * wh * P["high_amt"] + P["mid"][1] * wm)

    return gamut_map(L1, a1, b1)


def _fits(L1, a1, b1, m):
    lab = np.stack([L1, a1 * m, b1 * m], -1)
    _, lin = L.oklab_to_srgb(lab)
    return np.all((lin >= -2e-4) & (lin <= 1 + 2e-4), axis=-1)


def gamut_map(L1, a1, b1):
    """Reduce chroma at constant L and hue until the colour fits sRGB.

    The sRGB gamut is not convex along this path in OKLab, so scan from full chroma
    downward for the largest scale that fits, then refine by bisection."""
    L1 = np.clip(L1, 0, 1)
    best = np.zeros_like(L1)
    found = np.zeros(L1.shape, bool)
    prev = np.ones_like(L1)
    for m in np.linspace(1, 0, 41):
        ok = _fits(L1, a1, b1, m) & ~found
        best = np.where(ok, m, best)
        prev = np.where(ok, m + 0.025, prev)  # previous (failing) step above
        found |= ok
    lo, hi = best, np.minimum(prev, 1.0)
    for _ in range(10):
        mid = (lo + hi) / 2
        ok = _fits(L1, a1, b1, mid)
        lo = np.where(ok, mid, lo)
        hi = np.where(ok, hi, mid)
    lab = np.stack([L1, a1 * lo, b1 * lo], -1)
    srgb, _ = L.oklab_to_srgb(lab)
    return np.clip(srgb, 0, 1)


def build(name, P, base):
    out = grade(base, P)
    # force exact black/white behaviour: keep endpoints from drifting through the gamut mapper
    return np.clip(out, 0, 1)


def main():
    os.makedirs(OUT, exist_ok=True)
    base = L.load_png(BASE)
    for name, P in LOOKS.items():
        lut = build(name, P, base)
        L.save_png(lut, os.path.join(OUT, f"fb_{name}.lut.png"))
        L.save_cube(lut, os.path.join(OUT, f"fb_{name}.cube"), f"Flashback {P['title']}")
        print("wrote", name)


if __name__ == "__main__":
    main()
