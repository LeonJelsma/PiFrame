import logging
import os

import piexif
from PIL import Image, ImageEnhance, ImageFont, ImageDraw

from const import DISPLAY_HEIGHT, DISPLAY_WIDTH, FONTS_DIR
from utils.open_street_map_utils import coords_to_address

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def enhance_colors(image, brightness=1.1, contrast=1.2, saturation=1.5):
    """
    Enhance an image for e-ink display to make colors pop.

    Args:
        image (PIL.Image.Image): Input RGB image.
        brightness (float): Brightness factor (>1 brighter, <1 darker)
        contrast (float): Contrast factor (>1 stronger, <1 weaker)
        saturation (float): Color saturation factor (>1 more saturated)

    Returns:
        PIL.Image.Image: Enhanced image
    """
    img = image.convert("RGB")

    # Adjust brightness
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(brightness)

    # Adjust contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast)

    # Adjust saturation (color)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(saturation)

    return img


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
    target_ratio = DISPLAY_WIDTH / DISPLAY_HEIGHT

    # Determine new size
    if img_ratio > target_ratio:
        # Image is wider than target → fit width
        new_width = DISPLAY_WIDTH
        new_height = round(DISPLAY_WIDTH / img_ratio)
    else:
        # Image is taller than target → fit height
        new_height = DISPLAY_HEIGHT
        new_width = round(DISPLAY_HEIGHT * img_ratio)

    # Resize with high-quality resampling
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)

    # Create white background
    background = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT), (255, 255, 255))

    # Paste resized image centered
    x_offset = (DISPLAY_WIDTH - new_width) // 2
    y_offset = (DISPLAY_HEIGHT - new_height) // 2
    background.paste(img_resized, (x_offset, y_offset))

    return background


def count_images(path: str, recursive: bool = False) -> int:
    """Return the number of image files in a directory.

    Args:
        path (str): directory to scan (e.g. /mnt/nas/photos)
        recursive (bool): scan subdirectories if True

    Returns:
        int: number of image files found
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}
    count = 0

    if recursive:
        for root, _, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[1].lower() in image_extensions:
                    count += 1
    else:
        for file in os.listdir(path):
            if os.path.splitext(file)[1].lower() in image_extensions:
                count += 1

    return count


def image_generator(path: str):
    """
    Generator that yields PIL.Image objects for every image found in `path`.

    Args:
        path (str): directory to read images from
        recursive (bool): include subdirectories if True
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}

    for file in os.listdir(path):
        ext = os.path.splitext(file)[1].lower()
        if ext in image_extensions:
            full_path = os.path.join(path, file)
            try:
                image = Image.open(full_path)
                copy = image.copy()
                image.close()

                yield copy
            except Exception as e:
                print(f"⚠️ Skipping {file}: {e}")


def force_portrait(img: Image.Image) -> Image.Image:
    """
    Rotate image so that the *shorter side* is vertical (portrait)
    and the longer side is horizontal.
    """
    width, height = img.size

    # If the short side is currently horizontal, rotate
    if width < height:
        # Already portrait, do nothing
        return img
    else:
        # Rotate 90° clockwise to put the short side down
        return img.rotate(90, expand=True)


def add_metadata_overlay(img: Image.Image) -> Image.Image:
    """
    Reads EXIF date and GPS location from a PIL image,
    and draws it in the bottom-right corner.
    """
    img = img.copy()
    draw = ImageDraw.Draw(img)

    # Try to load a simple font
    try:
        font = ImageFont.truetype(os.path.join(FONTS_DIR, 'FunnelSans-VariableFont_wght.ttf'), 18)
    except:
        logger.error("Failed to load font, using system default")
        font = ImageFont.load_default()

    date_str = ""
    gps_str = ""

    # Extract EXIF
    try:
        exif_dict = piexif.load(img.info.get("exif", b""))
        # Date
        date_bytes = exif_dict["0th"].get(piexif.ImageIFD.DateTime)
        if date_bytes:
            date_str = date_bytes.decode("utf-8")

        # GPS
        gps_ifd = exif_dict.get("GPS", {})
        if gps_ifd:
            def dms_to_deg(dms, ref):
                deg = dms[0][0] / dms[0][1]
                min = dms[1][0] / dms[1][1]
                sec = dms[2][0] / dms[2][1]
                val = deg + min / 60 + sec / 3600
                if ref in [b"S", b"W"]:
                    val = -val
                return val

            lat = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
            lat_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef)
            lon = gps_ifd.get(piexif.GPSIFD.GPSLongitude)
            lon_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef)

            if lat and lat_ref and lon and lon_ref:
                lat_val = dms_to_deg(lat, lat_ref)
                lon_val = dms_to_deg(lon, lon_ref)
                gps_str = coords_to_address(lat_val, lon_val)

    except Exception as e:
        print(f"Failed to read EXIF metadata: {e}")

    text = f"{date_str} {gps_str}".strip()
    if text:
        # Draw semi-transparent rectangle for readability
        text_width, text_height = draw.textsize(text, font=font)
        padding = 4
        x = img.width - text_width - padding
        y = img.height - text_height - padding

        draw.rectangle(
            [(x - padding, y - padding), (img.width, img.height)],
            fill=(255, 255, 255, 128)  # white background
        )
        draw.text((x, y), text, fill=(0, 0, 0), font=font)

    return img
