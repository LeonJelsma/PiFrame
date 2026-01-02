import sys
from types import ModuleType

from PIL import Image

from const import SPECTRA6_PALETTE

# Create a dummy 'epdconfig' module
epdconfig = ModuleType("epdconfig")
epdconfig.EPD_SCK_PIN = 11
epdconfig.EPD_MOSI_PIN = 10
epdconfig.EPD_CS_M_PIN = 8
epdconfig.EPD_CS_S_PIN = 7
epdconfig.EPD_DC_PIN = 25
epdconfig.EPD_RST_PIN = 17
epdconfig.EPD_BUSY_PIN = 24
epdconfig.EPD_PWR_PIN = 18
sys.modules["lib.epdconfig"] = epdconfig

from lib import epd13in3E
from utils.image_utils import pre_process_image



# Open image
disk_image = Image.open("./test.jpeg")
image = disk_image.copy()
disk_image.close()

# Process image to buffer
screen = epd13in3E.EPD()
image = pre_process_image(image, "./test.jpeg")

image.show()
print('')
