import os
import time

from PIL import Image

from const import IMAGES_DIR
from lib import epd13in3E

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

EPD_WIDTH = 1200
EPD_HEIGHT = 1600

screen = epd13in3E.EPD()


def resize_for_spectra6(image):
    """
    Resize a PIL.Image to fit the Spectra 6 display (1200x1600) while keeping aspect ratio,
    and pad with white if needed.

    Args:
        image (PIL.Image.Image): Input image.

    Returns:
        PIL.Image.Image: Resized and padded image.
    """
    img = image.convert("RGB")  # ensure RGB

    # Calculate aspect ratios
    img_ratio = img.width / img.height
    target_ratio = EPD_WIDTH / EPD_HEIGHT

    # Determine new size
    if img_ratio > target_ratio:
        # Image is wider than target → fit width
        new_width = EPD_WIDTH
        new_height = round(EPD_WIDTH / img_ratio)
    else:
        # Image is taller than target → fit height
        new_height = EPD_HEIGHT
        new_width = round(EPD_HEIGHT * img_ratio)

    # Resize with high-quality resampling
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)

    # Create white background
    background = Image.new("RGB", (EPD_WIDTH, EPD_HEIGHT), (255, 255, 255))

    # Paste resized image centered
    x_offset = (EPD_WIDTH - new_width) // 2
    y_offset = (EPD_HEIGHT - new_height) // 2
    background.paste(img_resized, (x_offset, y_offset))

    return background


try:
    screen.Init()
    print("clearing...")
    screen.Clear()

    # Reading Image
    print("Drawing test.JPEG")
    image = Image.open(os.path.join(IMAGES_DIR, 'test.JPEG'))
    screen.display(screen.getbuffer(resize_for_spectra6(image)))

    print("Waiting 30 seconds before clearing")
    time.sleep(30)

    print("clearing...")
    screen.Clear()

    print("Going to sleep...")
    screen.sleep()
except Exception as e:
    print(f"Encountered error, going to sleep: {e}")
    screen.sleep()
