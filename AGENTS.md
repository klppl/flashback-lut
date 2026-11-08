# AGENTS.md

LUT generator for the Flashback ONE35 V2. Output must be importable by the Flashback phone app.

## Format (do not change)
- App LUT = 512×512 8-bit RGB PNG, 64³ CLUT in 8×8 tiles: pixel x = (b%8)*64 + r, y = (b//8)*64 + g. The app rejects larger files.
- `.cube` = 64³, red varies fastest. Generated only, git-ignored.

## Layout
- `tools/generator_template.html`: the whole web app (grade, UI, export). Edit this, never `lut_lab.html`.
- `tools/build_generator.py`: embeds base LUTs into the template, writes `lut_lab.html`. Re-run after every template edit and commit both.
- `tools/build_luts.py`, `lutlib.py`: Python version of the same grade. Keep its maths in sync with the JS `tone()`/`grade()`.
- `tools/validate.py`: checks neutral ramp monotonicity, step size, previews. Run after changing the grade.
- `luts/`: the app's own LUTs (extracted from the app bundle; Flashback's assets, keep the repo private or drop them before publishing).
- `custom/`: built looks. `demo_photos/`: public domain, credits in `CREDITS.md`.

## Design rules
- Every look = grade(base LUT), done in OKLab. The base (Classic v12 by default) keeps the app's exposure/encoding assumptions. Don't build LUTs from scratch assuming sRGB input.
- Clamp tone output to 0..1 before powers (negative base gave NaN once). Gamut-map by reducing chroma, never hard clip.
- Soft highlight shoulder (slope 1 at knee, 1.0 lands on white point). Don't lift blacks hard: the sensor is small and noisy.
- Python and JS must give the same LUT for the same params.

## Checks
- `python tools/build_luts.py && python tools/validate.py`, then `python tools/build_generator.py`.
- Open `lut_lab.html` over a local server (file:// is blocked in some browsers): run every preset, check no NaN/out-of-range values and a monotonic grey ramp.

## Not verified
- Exports have not been tested inside the app, nor on real camera photos.

## Safety
- Never edit the installed Flashback app or flash firmware. Reverse-engineering notes live in `docs/camera-notes.md`.
