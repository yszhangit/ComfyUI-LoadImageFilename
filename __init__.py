from .nodes import LoadImageWithFilename

NODE_CLASS_MAPPINGS = {
    "LoadImageWithFilename": LoadImageWithFilename,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageWithFilename": "Load Image (Filename)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
