# flashback-lut

An unofficial, browser-based LUT generator for the **Flashback ONE35 V2** camera. Pick a base, shape a look with a handful of film-style controls, and export a `.lut.png` that the Flashback phone app imports.

**Try it: https://klppl.github.io/flashback-lut/**

The camera can't load LUTs; the phone app applies them. This tool only makes the file.

> **Experimental.** The grade is verified (the Python and browser versions match, presets render cleanly), but I haven't yet confirmed that an exported PNG imports in the app, or tuned the looks on real ONE35 V2 photos. If you try one, please [open an issue](https://github.com/klppl/flashback-lut/issues) with what happened.

## How to use

1. Open the page, leave the base on **Classic v12**, pick a preset or hit **Randomize**.
2. Drag the divider on the demo photo (or **Open photo…** for your own) to compare, and tweak the sliders.
3. **Export LUT** and save the `.lut.png`.
4. Sync the file to your phone and import it in the Flashback app.

## What it does

- 16 presets (Sodium Dusk, Cold Flash, Cream Halation, Tungsten 800, Fade 400, B&W and more), a seeded **Randomize** (the seed reproduces the look) and **Nudge** for small variations
- Live before/after slider on demo photos or your own (photos never leave the page)
- Controls: tone (lift, contrast, pivot, highlight knee, white point), saturation, shadow/mid/highlight split toning, 7-band hue mixer, skin protection
- Export `.lut.png` (app), `.cube` (Lightroom, DaVinci Resolve, …) and a `.json` preset to keep editing later
- Use any app LUT as the base via **Load base…**

## How it works

Every look is `grade(base LUT)`. The base (Classic v12 by default) carries the app's own exposure and encoding assumptions, so the grade is applied on top of it instead of building a LUT from scratch.

- **Space:** the grade runs in OKLab. Lightness goes through a lift, an S-curve around a pivot and a soft shoulder (slope 1 at the knee, 1.0 lands on the white point). Chroma, hue shifts and tints are applied in the same space, with hue-band gaussians and a skin-tone guard.
- **Gamut:** out-of-range colours are mapped by reducing chroma, never hard-clipped.
- **Blacks:** lift is deliberately gentle; the sensor is small and noisy.
- **Preview vs export:** the preview samples a 33³ grid for speed; export bakes the full 64³ grid.

### LUT format

| | |
|---|---|
| App LUT | 512×512, 8-bit RGB PNG. The app rejects larger files. |
| Layout | 64³ CLUT in 8×8 tiles: `x = (b % 8) * 64 + r`, `y = (b // 8) * 64 + g` |
| `.cube` | 64³, red varies fastest |

## Repo layout

| Path | |
|---|---|
| `tools/generator_template.html` | The whole web app (grade, UI, export). Edit this, never `lut_lab.html`. |
| `tools/build_generator.py` | Embeds the base LUTs and writes `lut_lab.html` (or `site/index.html` with `--public`) |
| `tools/build_luts.py`, `lutlib.py` | Python version of the same grade |
| `tools/validate.py` | Grey-ramp monotonicity, step size, previews |
| `luts/` | The app's own base LUTs (Flashback's files) |
| `custom/` | Built looks |
| `demo_photos/` | Test photos, credits in `CREDITS.md` |
| `docs/camera-notes.md` | Reverse-engineering notes on the camera and app |

## Contributing

Pull requests are welcome: new presets, better controls, fixes, docs. Open an issue first for anything big. Real ONE35 V2 negatives and notes on how an exported LUT behaves in the app are especially useful.

## License

Code: [Lagom License](LICENSE). This does not cover the base LUTs in `luts/` (and `custom/` looks built from them), which are Flashback's files, or the demo photos (see `demo_photos/CREDITS.md`). Not affiliated with Flashback.
