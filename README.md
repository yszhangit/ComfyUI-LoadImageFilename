# ComfyUI Load Image (Filename)

Adds one node, `Load Image (Filename)` (category `image`), to ComfyUI.

It is ComfyUI's built-in `Load Image` node plus a third output: the loaded file's
name without its extension (`photo.png` -> `photo`). The node subclasses
`nodes.LoadImage`, so the dropdown, upload button, image decoding, video and
animated image support, `IS_CHANGED` and `VALIDATE_INPUTS` all come from core.
There is no PIL, torch or numpy code here.

## Outputs

| Name | Type | Description |
| --- | --- | --- |
| `image` | IMAGE | The loaded image tensor. |
| `mask` | MASK | The image mask, same as the built-in node. |
| `filename` | STRING | File name without extension. |

## Feeding Save Image

1. Add the node and pick an image.
2. On `Save Image`, right-click the `filename_prefix` widget and choose
   **Convert Widget to Input**.
3. Link `filename` into it.

ComfyUI still appends its own counter and extension, so `photo` becomes
`photo_00001_.png`.

## After changing this node

Custom nodes are imported once at startup, so the server must be restarted. The
browser tab caches the node list separately, so hard-refresh it
(Ctrl+Shift+R) as well.
