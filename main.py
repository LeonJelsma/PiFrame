import logging
import threading
import time

from fastapi import FastAPI

from const import IMAGE_DELAY_SECONDS, ImageCollection
from lib import epd13in3E
from utils.image_utils import enhance_colors, resize_for_spectra6, correct_image_orientation, \
    get_random_image, sharpen

screen = epd13in3E.EPD()

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)

CURRENT_IMAGE_COLLECTION: ImageCollection = ImageCollection.DEFAULT

next_image_trigger = threading.Event()


@app.post("/next")
def next_image():
    next_image_trigger.set()

    logger.info(f"Received manual trigger to display next image")
    return {"status": "ok"}


@app.post("/collection/{name}")
def set_collection(name: str):
    global CURRENT_IMAGE_COLLECTION

    CURRENT_IMAGE_COLLECTION = ImageCollection(name)
    next_image_trigger.set()

    logger.info(f"Switched image collection to {CURRENT_IMAGE_COLLECTION.name}")
    return {
        "status": "ok",
    }


def slideshow():
    try:
        global CURRENT_IMAGE_COLLECTION
        logger.info("PiFrame started, initializing display")

        screen.Init()
        screen.Clear()

        while True:
            image, image_path = get_random_image(CURRENT_IMAGE_COLLECTION.path())
            if image is None:
                print("No images found, waiting...")
                time.sleep(5)
                continue

            logger.info(f"Drawing next image: {image_path}")

            # Prepare image
            image = correct_image_orientation(image, image_path)
            image = enhance_colors(image)
            image = resize_for_spectra6(image)
            image = sharpen(image)

            # image = add_metadata_overlay(image, image_path)

            screen.display(screen.get_buffer(image))

            # Free up memory
            del image

            logger.info(f"Done, waiting {IMAGE_DELAY_SECONDS} seconds")

            next_image_trigger.wait(timeout=IMAGE_DELAY_SECONDS)
            next_image_trigger.clear()

        # This should not be reachable!
        logger.info("Out of images, clearing screen...")
        screen.Clear()

        logger.info("Going to sleep...")
        screen.sleep()
    except Exception as e:
        logger.error(f"Encountered error, going to sleep: {e}")
        screen.sleep()


threading.Thread(target=slideshow, daemon=True).start()
