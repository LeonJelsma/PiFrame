import os
from enum import Enum

import numpy as np

ROOT_DIR = os.getcwd()
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR = os.path.abspath('/mnt/frame-images')

DISPLAY_WIDTH = 1200
DISPLAY_HEIGHT = 1600

IMAGE_DELAY_SECONDS = 1200

# Dither palette mapping to driver/spectra6 palette
DITHER_TO_DRIVER = np.array([0, 1, 2, 3, 5, 6], dtype=np.uint8)

SPECTRA6_DRIVER_PALETTE = (
    25, 30, 33,  # 0 Black
    232, 232, 232,  # 1 Off-White
    239, 222, 68,  # 2 Yellow
    178, 19, 24,  # 3 Red
    25, 30, 33,  # 4 Extra Black (same as black)
    33, 87, 186,  # 5 Blue
    18, 95, 32  # 6 Green
)

SPECTRA6_DITHER_PALETTE = (
    25, 30, 33,  # 0 Black
    232, 232, 232,  # 1 Off-White
    239, 222, 68,  # 2 Yellow
    178, 19, 24,  # 3 Red
    33, 87, 186,  # 4 Blue
    18, 95, 32  # 5 Green
)


class ImageCollection(Enum):
    DEFAULT: str = "default"
    RICO: str = "rico"
    MENG: str = "meng"

    def path(self) -> str:
        if self is ImageCollection.DEFAULT:
            return IMAGES_DIR

        return os.path.join(IMAGES_DIR, self.value)
