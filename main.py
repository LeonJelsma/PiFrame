import logging
import time

from const import IMAGES_DIR, IMAGE_DELAY_SECONDS
from lib import epd13in3E
from utils.image_utils import enhance_colors, resize_for_spectra6, correct_image_orientation, \
    get_random_image

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

    while True:
        image, image_path = get_random_image(IMAGES_DIR)
        if image is None:
            print("No images found, waiting...")
            time.sleep(5)
            continue

        logger.info(f"Drawing next image: {image_path}")

        # Prepare image
        image = correct_image_orientation(image, image_path)
        image = enhance_colors(image)
        image = resize_for_spectra6(image)

        # image = add_metadata_overlay(image, image_path)

        screen.display(screen.get_buffer(image))

        # Free up memory
        del image

        logger.info(f"Done, waiting {IMAGE_DELAY_SECONDS} seconds")
        time.sleep(IMAGE_DELAY_SECONDS)

    # This should not be reachable!
    logger.info("Out of images, clearing screen...")
    screen.Clear()

    logger.info("Going to sleep...")
    screen.sleep()
except Exception as e:
    logger.error(f"Encountered error, going to sleep: {e}")
    screen.sleep()
