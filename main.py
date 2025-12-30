import logging
import os
import time

from PIL import Image

from const import IMAGES_DIR
from lib import epd13in3E
from utils.image_utils import enhance_colors, resize_for_spectra6, count_images, image_generator

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

screen = epd13in3E.EPD()

logger = logging.getLogger(__name__)

try:
    screen.Init()
    logger.info("PiFrame started!")
    screen.Clear()

    for image_path in image_generator(IMAGES_DIR):
        print("Drawing test.JPEG")
        image = Image.open(os.path.join(image_path))
        image = enhance_colors(image)
        image = resize_for_spectra6(image)
        screen.display(screen.getbuffer(image))
        time.sleep(30)

    print("clearing...")
    screen.Clear()

    print("Going to sleep...")
    screen.sleep()
except Exception as e:
    print(f"Encountered error, going to sleep: {e}")
    screen.sleep()
