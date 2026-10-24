# ComfyUI Load Image (Filename)

Adds one node, `Load Image (Filename)` (category `image`), to ComfyUI.

It is ComfyUI's built-in `Load Image` node plus a third output: the loaded file's
name without its extension (`photo.png` -> `photo`). The node subclasses
`nodes.LoadImage`, so the dropdown, upload button, image decoding, video and
animated image support, `IS_CHANGED` and `VALIDATE_INPUTS` all come from core.
There is no PIL, torch, or numpy code here.

## Installation

Install through ComfyUI Manager, or clone into `custom_nodes`:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/yszhangit/ComfyUI-LoadImageFilename
```

No dependencies. Restart ComfyUI afterwards.

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `image` | IMAGE | The loaded image tensor. |
| `mask` | MASK | The image mask, same as the built-in node. |
| `filename` | STRING | File name without extension. |

## Typical use case: feeding Save Image

Use the input file's name as part of the output file's name.

1. Add the node and pick an image.
2. Connect `filename` into `Save Image`'s `filename_prefix` (directly, or via a
   text-concat node to add your own prefix/postfix).
3. The saved file is named after the sanitized `filename` output.

## Toggles

Two independent boolean inputs control the `filename` output. Each is part of
`IS_CHANGED`, so flipping a toggle re-runs the node and refreshes the output.

### `sanitize_filename` (on by default)

Removes everything that must not appear in a file name or directory component:

- Control characters: newline `\n`, carriage return, tab, NUL, DEL, and Unicode
  control/format characters (zero-width joins, soft hyphen, …).
- Path separators `/` and `\`, and the reserved set `: * ? " < > |`.
- Leading/trailing dots and spaces (hidden-file leading dots, the trailing
  `.`/space Windows rejects).

Interior spaces and non-ASCII letters (Chinese, accented letters, …) are kept —
only unsafe characters are dropped. Turning this off returns the raw name.

### `filter_emoji` (off by default)

Removes emoji and emoji joiners: the pictograph / emoticon / symbol blocks, flag
regional indicators, variation selectors, the zero-width joiner, combining
keycap, and common symbol singles (`© ® ™ ✅ ❌ ⭐` …). Independent of sanitize —
enable it on top of sanitize to drop emoji too, or alone to strip emoji while
leaving control and reserved characters untouched.

## Regex manipulation

`pattern` + `replacement` run `re.sub(pattern, replacement, filename)` on the
name, **before** the emoji and sanitize steps. Leave `pattern` empty for the
plain behavior.

- **Strip a counter** — `pattern = _+\d+_*` with an empty replacement turns
  `ComfyUI_00001_` into `ComfyUI` and `slot_001` into `slot`.
- **Rename fully** — `pattern = ^.*$`, replacement = the new name.
- **Groups** — `replacement` supports captures: `pattern = (\d+)` and
  `replacement = [\1]` brackets the digits.

Sanitize runs last, so a replacement can't inject a `/` into the saved name. An
invalid pattern (e.g. `(`) reports a clear node error; a pattern that matches
nothing leaves the name unchanged.

### Live preview

Every time the node runs it reports the match in its preview panel as a **text**
preview (`ui.text`): `SOURCE`, `PATTERN`, `MATCHED`, and `RESULT`, with control
characters shown as visible escapes (a newline appears as `\n`). It uses the text
preview channel, so the node's own loaded-image preview is left untouched — no
image card, no Pillow, no temp files, no frontend code.

## Common patterns

Python `re` syntax. The result below is the regex step; the `sanitize_filename`
toggle then strips control/path/reserved characters (so a replacement can't
inject a `/`), and `filter_emoji` (if on) removes emoji.

| Source name | `pattern` | `replacement` | Result |
| --- | --- | --- | --- |
| `ComfyUI_00001_` | `_+\d+_*` | *(empty)* | `ComfyUI` |
| `slot_001` | `_+\d+_*` | *(empty)* | `slot` |
| `DSC_0420` | `_?\d+$` | *(empty)* | `DSC` |
| `001_photo` | `^\d+_?` | *(empty)* | `photo` |
| `2024-01-15_photo` | `^\d{4}-\d{2}-\d{2}_?` | *(empty)* | `photo` |
| `slot_001_v2` | `_.*$` | *(empty)* | `slot` |
| `a_b_c` | `^.*_` | *(empty)* | `c` |
| `photo copy 2` | ` copy \d+$` | *(empty)* | `photo` |
| `my cool pic` | `\s+` | `_` | `my_cool_pic` |
| `a___b` | `_{2,}` | `_` | `a_b` |
| `img00042png` | `[^0-9]+` | *(empty)* | `00042` |
| `verylongfilename123456` | `^(.{12}).*$` | `\1` | `verylongfile` |
| *(any name)* | `^.*$` | `myname` | `myname` |
| `photo` | `^` | `myapp_` | `myapp_photo` (prepend) |
| `photo` | `$` | `-2024-05-01` | `photo-2024-05-01` (append) |
| `photo` | `^.*$` | `pre-\g<0>-suf` | `pre-photo-suf` (wrap) |

- **Strip a counter** — `_+\d+_*` (trailing), `^\d+_?` (leading). The `$`/`^`
  anchors keep it from eating a middle `_1_`.
- **Rename fully** — `^.*$` + the new name in `replacement`.
- **Prepend / append / wrap** — pattern `^` prepends to `replacement`; pattern
  `$` appends. Wrap both with `^.*$` and `replacement = pre-\g<0>-suf`. The whole
  match is `\g<0>` — **not** `\0` (which is a NUL byte).
- **Keep first N chars** — `^(.{N}).*$` with `replacement = \1`.
- **Groups** — `replacement` supports `\1`, `\2`, … referencing capture groups.

## Test workflow

[`test-workflow.json`](test-workflow.json) is a ready graph: a
`Load Image (Filename)` node wired into `Save Image`'s `filename_prefix`, plus a
Note listing the toggle matrix. Drag it onto the canvas, pick an input whose name
contains a newline, `:` or `/` (upload one), and confirm the saved file is named
by the sanitized output. The node also carries `pattern` / `replacement` (the
sample prefills `_+\d+_*` to strip a trailing counter), and its preview card
shows the match and result every load. Toggle the booleans, or edit the pattern,
to watch the filename change.

![Sample workflow: the filename output feeding the Save Image filename_prefix](load-image-filename-workflow-sample.png)

In the sample above the prefix `qwen_edit/qie_` is joined with the `filename`
output of `slot_01_00002_.png`, so `Save Image` writes into
`output/qwen_edit/qie_slot_01_00002_...png`.

## Inspired by

[thalismind/ComfyUI-LoadImageWithFilename](https://github.com/thalismind/ComfyUI-LoadImageWithFilename),
which outputs the file name alongside folder loading and a file-name driven
`Save Image`. This pack is an independent minimal implementation: it subclasses
ComfyUI's own `LoadImage` rather than copying the decode and save code.

## License

GPL-3.0, matching ComfyUI itself. See [LICENSE](LICENSE).

