# flashback-lut

LUT generator for the Flashback ONE35 V2 camera. Makes `.lut.png` files (512×512, 64³) that the Flashback app imports, plus `.cube` for desktop editors.

## Use

Open `lut_lab.html` in a browser. Pick a base and preset (or hit Randomize), tweak, then **Save .lut.png**. AirDrop it to the iPhone's Files app and import it in the Flashback app. The camera itself can't load LUTs.

## GitHub Pages

`.github/workflows/pages.yml` builds `python tools/build_generator.py --public` and deploys `site/` on every push to `main` that touches `tools/`. The public build embeds only the identity base (33 KB page), not Flashback's own LUTs in `luts/`. To turn it on: repo Settings → Pages → Source: **GitHub Actions**. The full 6 MB `lut_lab.html` stays local.

## Rebuild

```bash
pip install -r requirements.txt
python tools/build_luts.py       # custom/ looks (png + cube)
python tools/build_generator.py  # lut_lab.html
```

## Layout

`tools/` generators · `luts/` base LUTs from the app · `custom/` built looks · `demo_photos/` public-domain test photos · `docs/` camera notes
