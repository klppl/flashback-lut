"""Embed base LUTs into the generator template -> lut_lab.html (single self-contained file)."""
import base64, json, os, sys, io
sys.path.insert(0, os.path.dirname(__file__))
import lutlib as L
R = os.path.join(os.path.dirname(__file__), "..")
bases = {
    "classic": ("Classic v12", "luts/classicv12balance.lut.png"),
    "beta": ("Beta v6", "luts/betav6princeedwardstation.lut.png"),
    "gold": ("Gold", "luts/goldwithRGBcurvesv2.lut.png"),
    "retrohaze": ("Retro Haze", "luts/purpleorangeretrohazev2.lut.png"),
    "disposable": ("Disposable", "luts/rawed_disposable_evm0.75.lut.png"),
}
# --public: write to site/index.html (for GitHub Pages) instead of lut_lab.html.
# --no-bases: embed only the identity base (the app's own LUTs are Flashback's files).
PUBLIC = "--public" in sys.argv
if "--no-bases" in sys.argv:
    bases = {}
out = {}
for k, (label, p) in bases.items():
    out[k] = {"label": label, "uri": "data:image/png;base64," + base64.b64encode(open(os.path.join(R, p), "rb").read()).decode()}
tmp = os.path.join(R, "tools", "_identity.png"); L.save_png(L.identity(), tmp)
out["identity"] = {"label": "Identity (no base)", "uri": "data:image/png;base64," + base64.b64encode(open(tmp, "rb").read()).decode()}
os.remove(tmp)
html = open(os.path.join(R, "tools", "generator_template.html")).read().replace("/*BASES*/", "const BASES = " + json.dumps(out) + ";")
if PUBLIC:
    os.makedirs(os.path.join(R, "site"), exist_ok=True)
    dest = os.path.join("site", "index.html")
    open(os.path.join(R, "site", ".nojekyll"), "w").close()
    import shutil
    shutil.copytree(os.path.join(R, "demo_photos"), os.path.join(R, "site", "demo_photos"), dirs_exist_ok=True)
else:
    dest = "lut_lab.html"
open(os.path.join(R, dest), "w").write(html)
print("wrote", dest, len(html) // 1024, "KB")
