import os

import folder_paths
from nodes import LoadImage


class LoadImageWithFilename(LoadImage):
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "mask", "filename")
    CATEGORY = "image"
    DESCRIPTION = "Loads an image and outputs the file name without its extension."
    SEARCH_ALIASES = ["load image filename", "image filename", "image name"]

    def load_image(self, image):
        images, mask = super().load_image(image)
        filename = os.path.splitext(os.path.basename(folder_paths.get_annotated_filepath(image)))[0]
        return (images, mask, filename)
