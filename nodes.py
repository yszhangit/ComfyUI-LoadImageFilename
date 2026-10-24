import os
import re
import unicodedata

import folder_paths
from nodes import LoadImage

# Characters that must never reach a file name: path separators, the
# Windows-reserved set, and NUL. Everything control- or format-like (newline,
# tab, carriage return, zero-width joins) is dropped by Unicode category.
# Leading/trailing dots and spaces are stripped so the value is a bare, safe
# component for Save Image's filename_prefix.
_RESERVED_CHARS = '\\/:*?"<>|'
_CONTROL_CATEGORIES = frozenset(("Cc", "Cf", "Co", "Cs"))


def _sanitize_filename(name):
    name = "".join(c for c in name if unicodedata.category(c) not in _CONTROL_CATEGORIES)
    name = "".join(c for c in name if c not in _RESERVED_CHARS)
    return name.strip().strip(".").strip().strip(".")


# Broad emoji coverage: the pictograph / emoticon / symbol blocks (which also
# contain the flag regional indicators), plus the variation selectors, zero-width
# joiner and combining keycap that make up multi-code-point emoji sequences.
_EMOJI_RANGES = (
    (0x1F000, 0x1FBFF),
    (0x2300, 0x23FF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
    (0xFE00, 0xFE0F),
    (0x200D, 0x200D),
    (0x20E3, 0x20E3),
)
_EMOJI_SINGLES = "©®‼⁉™ℹ↩↪⛎▪▫▶◀◻◼◽◾⤴⤵〰〽㊗㊙"
_EMOJI_RE = re.compile(
    "[" + "".join(chr(lo) + "-" + chr(hi) for lo, hi in _EMOJI_RANGES) + _EMOJI_SINGLES + "]"
)


def _filter_emoji(name):
    return _EMOJI_RE.sub("", name)


def _apply_regex(name, pattern, replacement):
    # Empty pattern leaves the name untouched. A malformed pattern, or a
    # replacement naming a group the pattern does not define, surfaces as a
    # plain ValueError so the node reports a clear error, not a traceback.
    if not pattern:
        return name, []
    try:
        rx = re.compile(pattern)
        result = rx.sub(replacement, name)
        matches = [m.span() for m in rx.finditer(name)]
    except re.error as ex:
        raise ValueError("Invalid regex pattern/replacement {!r}: {}".format(pattern, ex)) from ex
    return result, matches


def _preview_text(text):
    # Preview is a display surface: render control, format, private-use and
    # surrogate characters as visible escapes so each field stays on one line
    # and never carries a lone surrogate a text widget cannot show.
    out = []
    for c in text:
        cat = unicodedata.category(c)
        if c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif c == "\r":
            out.append("\\r")
        elif cat in _CONTROL_CATEGORIES:
            out.append("\\u{:04X}".format(ord(c)))
        else:
            out.append(c)
    return "".join(out)


def _preview_text_block(source, pattern, matches, result):
    # ui.text preview channel: the regex-match report, shown without touching
    # the node's own image preview.
    matched = " ".join(_preview_text(source[s:e]) for s, e in matches if s < e)
    return "SOURCE:  {}\nPATTERN: {}\nMATCHED: {}\nRESULT:  {}".format(
        _preview_text(source),
        _preview_text(pattern) or "(none)",
        matched or "(no match)",
        _preview_text(result),
    )


class LoadImageFilename(LoadImage):
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "mask", "filename")
    CATEGORY = "image"
    DESCRIPTION = (
        "Loads an image and outputs the file name without its extension. "
        "'sanitize filename' (on by default) drops control characters "
        "(newline, tab, carriage return), path separators and file-system "
        "reserved characters, and trims leading/trailing dots and spaces. "
        "'filter emoji' (off by default) additionally removes emoji and "
        "emoji joiners. 'pattern'/'replacement' run re.sub on the name first "
        "(full rename is pattern '^.*$'); sanitize runs last, so a replacement "
        "cannot inject a path separator."
    )
    SEARCH_ALIASES = ["load image filename", "image filename", "image name", "sanitize filename"]

    @classmethod
    def INPUT_TYPES(s):
        inputs = super().INPUT_TYPES()
        optional = inputs.setdefault("optional", {})
        optional["sanitize_filename"] = ("BOOLEAN", {"default": True})
        optional["filter_emoji"] = ("BOOLEAN", {"default": False})
        optional["pattern"] = ("STRING", {"default": "", "multiline": True})
        optional["replacement"] = ("STRING", {"default": ""})
        return inputs

    def load_image(self, image, sanitize_filename=True, filter_emoji=False, pattern="", replacement=""):
        images, mask = super().load_image(image)
        source = os.path.splitext(os.path.basename(folder_paths.get_annotated_filepath(image)))[0]
        filename, matches = _apply_regex(source, pattern, replacement)
        if filter_emoji:
            filename = _filter_emoji(filename)
        if sanitize_filename:
            filename = _sanitize_filename(filename)
        preview = _preview_text_block(source, pattern, matches, filename)
        return {"ui": {"text": (preview,)}, "result": (images, mask, filename)}

    @classmethod
    def IS_CHANGED(s, image, sanitize_filename=True, filter_emoji=False, pattern="", replacement=""):
        return super().IS_CHANGED(image) + str(sanitize_filename) + str(filter_emoji) + repr((pattern, replacement))
