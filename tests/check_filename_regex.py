import os
import sys
sys.path.insert(0, os.environ["COMFY_ROOT"])

# Force ComfyUI's CPU mode before importing the node module: comfy gates CLI
# parsing behind comfy.options.args_parsing (False on import), so sys.argv is
# ignored — set args.cpu directly. Without this, importing nodes.py probes GPU
# VRAM at import time and OOMs against the running server. Test-only harness.
import comfy.cli_args as _cli
_cli.args.cpu = True

# Load the pack's nodes.py by file path so the branch under test is the file
# being exercised (import_module("custom_nodes....") resolves the installed copy).
sys.path.insert(0, os.environ["COMFY_ROOT"])
_here = os.path.dirname(os.path.abspath(__file__))
import importlib.util
_spec = importlib.util.spec_from_file_location("lif_nodes", os.path.join(_here, "..", "nodes.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

import folder_paths
import numpy as np
import torch
from PIL import Image
import comfy.model_management as mm

# Test-only: keep load_image on the CPU so the headless checks do not touch the
# GPU the running ComfyUI server is holding.
mm.intermediate_device = lambda: torch.device("cpu")
mm.intermediate_dtype = lambda: torch.float32
Cls = m.LoadImageFilename


def _name(out):
    # load_image returns the {"ui", "result"} dict.
    return out["result"][2] if isinstance(out, dict) else out[2]


def _make(name):
    Image.fromarray((np.random.rand(4, 4, 3) * 255).astype("uint8")).save(
        os.path.join(folder_paths.get_input_directory(), name))
    return name


def _rm(name):
    os.remove(os.path.join(folder_paths.get_input_directory(), name))


# _apply_regex: substitution result + match spans, empty pattern, errors.
a = m._apply_regex
assert a("slot_001", r"_+\d+$", "") == ("slot", [(4, 8)])
assert a("ComfyUI_00001_", r"_+\d+_*", "")[0] == "ComfyUI"
assert a("anything", r"^.*$", "myname") == ("myname", [(0, 8)])
assert a("photo", r"", "x") == ("photo", [])
assert a("photo", r"zzz", "X")[0] == "photo"
assert a("aXbXc", r"X", "1") == ("a1b1c", [(1, 2), (3, 4)])
assert a("foo12", r"(\d+)", r"[\1]") == ("foo[12]", [(3, 5)])
res, sp = a("ab", r"x*", "Z")
assert res.startswith("Z") and all(s == e for s, e in sp)
for bad in (("(", ""), (r"(\d)", r"\2")):
    try:
        a("x1", bad[0], bad[1]); assert False, "expected ValueError"
    except ValueError: pass

# _preview_text: control/format/surrogate chars become visible escapes.
pt = m._preview_text
assert pt("a\nb") == "a\\nb" and pt("a\tb") == "a\\tb"
pt("\udcff")                                                    # lone surrogate: no raise

# End-to-end: regex + sanitize pipeline, and a TEXT preview channel (ui.text).
name = _make("hello:world_00123.png")
try:
    out = Cls().load_image(name, sanitize_filename=True, filter_emoji=True,
                           pattern=r"_+\d+_*", replacement="")
    assert _name(out) == "helloworld", _name(out)            # counter stripped, ':' sanitized
    assert "images" not in out["ui"], "preview must not use the image channel"
    text = out["ui"]["text"][0]
    assert "SOURCE:" in text and "PATTERN:" in text and "RESULT:" in text
    assert "helloworld" in text
    assert len(out["result"]) == 4, out["result"]        # image, mask, filename, preview
    assert out["result"][3] == text                       # 4th output is the report string
finally:
    _rm(name)

# Output names: the report socket is named `match_report` (filename is the result).
assert Cls.RETURN_NAMES == ("image", "mask", "filename", "match_report"), Cls.RETURN_NAMES

# IS_CHANGED: distinct cache key per (pattern, replacement); no delimiter collisions.
slot = _make("slot.png")
try:
    i = Cls.IS_CHANGED
    assert i("slot.png", True, False, "ab", "c") != i("slot.png", True, False, "a", "bc")
    assert i("slot.png", True, False, r"(\d)1", "x") != i("slot.png", True, False, r"(\d)", "1x")
finally:
    _rm(slot)

# A lone-surrogate filename loads end-to-end; the preview must not crash the node.
bad = _make("bad\udcff_name.png")
try:
    out = Cls().load_image(bad)
    assert _name(out).startswith("bad"), _name(out)
    assert isinstance(out["ui"]["text"][0], str)
    assert len(out["result"]) == 4
finally:
    _rm(bad)

# allow_path_separator: keep '/', strip other reserved chars, block traversal.
sf = m._sanitize_filename
assert sf("a/b", False) == "ab"
assert sf("a/b", True) == "a/b"
assert sf("a\\b/c", True) == "ab/c"
assert sf("../../etc/passwd", True) == "etc/passwd"
assert sf("/etc/passwd", True) == "etc/passwd"
assert sf("a/./b/..", True) == "a/b"
assert sf(" qwen_edit/ qie. ", True) == "qwen_edit/qie"

photo = _make("photo.png")
try:
    out = Cls().load_image("photo.png", sanitize_filename=True, allow_path_separator=True,
                           pattern=r"^", replacement="qwen_edit/")
    assert _name(out) == "qwen_edit/photo", _name(out)
    out = Cls().load_image("photo.png", sanitize_filename=True, allow_path_separator=True,
                           pattern=r"^", replacement="../../")
    assert ".." not in _name(out) and not _name(out).startswith("/"), _name(out)
finally:
    _rm("photo.png")

print("ALL OK")
