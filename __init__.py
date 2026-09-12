from .nodes import LoadImageFilename

NODE_CLASS_MAPPINGS = {
    "LoadImageFilename": LoadImageFilename,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFilename": "Load Image (Filename)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
