import os
import time

from PIL import Image

from const import IMAGES_DIR
from lib import epd13in3E

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

screen = epd13in3E.EPD()


try:
    screen.Init()
    print("clearing...")
    screen.Clear()

    # Reading Image
    print("Drawing test.JPEG")
    Himage = Image.open(os.path.join(IMAGES_DIR, 'test.JPEG'))
    screen.display(screen.getbuffer(Himage))

    print("Waiting 30 seconds before clearing")
    time.sleep(30)

    print("clearing...")
    screen.Clear()

    print("Going to sleep...")
    screen.sleep()
except Exception as e:
    print(f"Encountered error, going to sleep: {e}")
    screen.sleep()
