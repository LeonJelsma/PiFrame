import logging
import time

from const import IMAGES_DIR
from lib import epd13in3E
from utils.image_utils import enhance_colors, resize_for_spectra6, image_generator, apply_exif_orientation

screen = epd13in3E.EPD()

logger = logging.getLogger(__name__)

try:
    logger.info("PiFrame started, initializing display")

    screen.Init()
    screen.Clear()

    for image in image_generator(IMAGES_DIR):
        logger.info("Drawing next image...")
        
        # Prepare image
        image = enhance_colors(image)
        image = resize_for_spectra6(image)
        image = apply_exif_orientation(image)

        screen.display(screen.getbuffer(image))
        time.sleep(30)

    logger.info("Out of images, clearing screen...")
    screen.Clear()

    logger.info("Going to sleep...")
    screen.sleep()
except Exception as e:
    logger.error(f"Encountered error, going to sleep: {e}")
    screen.sleep()
