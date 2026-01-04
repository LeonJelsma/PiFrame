import os
from enum import Enum

ROOT_DIR = os.getcwd()
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR = os.path.abspath('/mnt/frame-images')

DISPLAY_WIDTH = 1200
DISPLAY_HEIGHT = 1600

IMAGE_DELAY_SECONDS = 1200

SPECTRA6_COLORS = (
    0, 0, 0,  # Black
    250, 250, 250,  # Off-White (instead of 255)
    255, 255, 0,  # Yellow
    255, 0, 0,  # Red
    0, 0, 0,  # Extra Black (ignored)
    0, 0, 255,  # Blue
    0, 255, 0  # Green
)

SPECTRA6_PALETTE = (
    25, 30, 33,  # Black
    232, 232, 232,  # Off-White
    239, 222, 68,  # Yellow
    178, 19, 24,  # Red
    0, 0, 0,  # Extra Black (ignored)
    33, 87, 186,  # Blue
    18, 95, 32  # Green
)


class ImageCollection(Enum):
    DEFAULT: str = "default"
    RICO: str = "rico"
    MENG: str = "meng"

    def path(self) -> str:
        if self is ImageCollection.DEFAULT:
            return IMAGES_DIR

        return os.path.join(IMAGES_DIR, self.value)
