import logging
import time

from const import IMAGES_DIR, IMAGE_DELAY_SECONDS
from lib import epd13in3E
from utils.image_utils import enhance_colors, resize_for_spectra6, image_generator, force_portrait

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

    for image in image_generator(IMAGES_DIR):
        logger.info("Drawing next image...")

        # Prepare image
        image = enhance_colors(image)
        image = resize_for_spectra6(image)
        image = force_portrait(image)

        screen.display(screen.getbuffer(image))

        time.sleep(IMAGE_DELAY_SECONDS)
        logger.info(f"Done, waiting {IMAGE_DELAY_SECONDS} seconds")

    logger.info("Out of images, clearing screen...")
    screen.Clear()

    logger.info("Going to sleep...")
    screen.sleep()
except Exception as e:
    logger.error(f"Encountered error, going to sleep: {e}")
    screen.sleep()
