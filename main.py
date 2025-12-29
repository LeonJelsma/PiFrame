import os
import time

from PIL import Image

from const import IMAGES_DIR
from lib import epd13in3E

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

epd = epd13in3E.EPD()
try:
    epd.Init()
    print("clearing...")
    epd.Clear()

    # Drawing on the image
    print("1.Drawing on the image...")

    # read bmp file
    print("2.read bmp file")
    Himage = Image.open(os.path.join(IMAGES_DIR, 'test.JPEG'))
    epd.display(epd.getbuffer(Himage))
    time.sleep(30)

    print("clearing...")
    epd.Clear()

    print("goto sleep...")
    epd.sleep()
except:
    print("goto sleep...")
    epd.sleep()
