import os
from enum import Enum

ROOT_DIR = os.getcwd()
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR = os.path.abspath('/mnt/frame-images')

DISPLAY_WIDTH = 1200
DISPLAY_HEIGHT = 1600

IMAGE_DELAY_SECONDS = 1200


class ImageCollection(Enum):
    DEFAULT: str = "default"
    RICO: str = "rico"
    MENG: str = "meng"

    def path(self) -> str:
        if self is ImageCollection.DEFAULT:
            return IMAGES_DIR

        return os.path.join(IMAGES_DIR, self.value)