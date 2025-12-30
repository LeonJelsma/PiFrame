import logging
import time

from const import IMAGES_DIR, IMAGE_DELAY_SECONDS
from lib import epd13in3E
from utils.image_utils import enhance_colors, resize_for_spectra6, image_generator, correct_image_orientation, add_metadata_overlay

screen = epd13in3E.EPD()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)

try:
    logger.info("PiFrame started, initializing display")

    screen.Init()
    screen.Clear()

    for image, image_path in image_generator(IMAGES_DIR):
        logger.info("Drawing next image...")

        # Prepare image
        image = enhance_colors(image)
        image = resize_for_spectra6(image)
        image = correct_image_orientation(image, image_path)
        image = add_metadata_overlay(image, image_path)

        screen.display(screen.get_buffer(image))

        logger.info(f"Done, waiting {IMAGE_DELAY_SECONDS} seconds")
        time.sleep(IMAGE_DELAY_SECONDS)

    logger.info("Out of images, clearing screen...")
    screen.Clear()

    logger.info("Going to sleep...")
    screen.sleep()
except Exception as e:
    logger.error(f"Encountered error, going to sleep: {e}")
    screen.sleep()
