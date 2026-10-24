import os
import sys

# Load THIS worktree's nodes.py by file path: import_module("custom_nodes....")
# would resolve the installed master checkout, not the branch under test.
sys.path.insert(0, os.environ["COMFY_ROOT"])
_here = os.path.dirname(os.path.abspath(__file__))
import importlib.util
_spec = importlib.util.spec_from_file_location("lif_nodes", os.path.join(_here, "..", "nodes.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

a = m._apply_regex

assert a("slot_001", r"_+\d+$", "") == ("slot", [(4, 8)])
assert a("ComfyUI_00001_", r"_+\d+_*", "")[0] == "ComfyUI"
assert a("anything", r"^.*$", "myname") == ("myname", [(0, 8)])
assert a("photo", r"", "x") == ("photo", [])          # empty pattern: no-op
assert a("photo", r"zzz", "X")[0] == "photo"          # no match: unchanged
assert a("aXbXc", r"X", "1") == ("a1b1c", [(1, 2), (3, 4)])
assert a("foo12", r"(\d+)", r"[\1]") == ("foo[12]", [(3, 5)])
res, sp = a("ab", r"x*", "Z")          # zero-width: must not loop; spans are empty
assert res.startswith("Z") and all(s == e for s, e in sp)
for bad in (("(", ""), (r"(\d)", r"\2")):  # malformed pattern, and bad group reference
    try:
        a("x1", bad[0], bad[1]); assert False, "expected ValueError"
    except ValueError: pass

# End-to-end: the regex step feeds Save Image through load_image's filename output.
import folder_paths
import numpy as np
from PIL import Image
Cls = m.LoadImageFilename
_in = folder_paths.get_input_directory()
_names = ["slot_001.png", "shot_1_final.png"]
for _n in _names:
    Image.fromarray((np.random.rand(4, 4, 3) * 255).astype("uint8")).save(os.path.join(_in, _n))
try:
    assert Cls().load_image("slot_001.png", pattern=r"_+\d+$", replacement="")[2] == "slot"
    assert Cls().load_image("shot_1_final.png", pattern=r"_+\d+$", replacement="")[2] == "shot_1_final"
    try:
        Cls().load_image("slot_001.png", pattern="(", replacement="")
        assert False, "expected ValueError"
    except ValueError: pass
finally:
    for _n in _names:
        os.remove(os.path.join(_in, _n))

print("Task1 OK")
