# ComfyUI Load Image (Filename)

Adds one node, `Load Image (Filename)` (category `image`), to ComfyUI.

It is ComfyUI's built-in `Load Image` node plus a third output: the loaded file's
name without its extension (`photo.png` -> `photo`). The node subclasses
`nodes.LoadImage`, so the dropdown, upload button, image decoding, video and
animated image support, `IS_CHANGED` and `VALIDATE_INPUTS` all come from core.
There is no PIL, torch or numpy code here.

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

## Feeding Save Image Typical use case
includes the input filename into the output filename.

1. Add the node and pick an image.
2. Connect the `filename_prefix` to `Concatenate Text`, add your prefix or postfix.
3. Link `Concatenate Text` into `Save Image` filename.

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

