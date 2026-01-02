import logging
import os
import random

import piexif
from PIL import Image, ImageEnhance, ImageFont, ImageDraw, ExifTags, ImageFilter

from const import DISPLAY_HEIGHT, DISPLAY_WIDTH, FONTS_DIR, SPECTRA6_PALETTE
from utils.open_street_map_utils import coords_to_address

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


def pre_process_image(image: Image, image_path: str):
    image = correct_image_orientation(image, image_path)
    image = enhance_colors(image)
    image = resize_for_spectra6(image)
    image = sharpen(image)
    image = convert_to_spectra_palette(image)

    return image


def convert_to_spectra_palette(image: Image):
    pal_image = Image.new("P", (1, 1))
    palette = SPECTRA6_PALETTE + (0, 0, 0) * 249  # Fill remaining palette entries
    pal_image.putpalette(palette)

    # Quantize image to 7 colors with dithering
    image = image.convert("RGB").quantize(
        palette=pal_image,
        dither=Image.FLOYDSTEINBERG
    )

    return image


def sharpen(image, amount=1.2, radius=1.0):
    return image.filter(ImageFilter.UnsharpMask(radius=radius, percent=int(amount * 100), threshold=3))


def enhance_colors(image, brightness=1.2, contrast=1.0, saturation=1.1):
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


def get_random_image(path: str):
    """
    Return a single random image from the directory, along with its full path.

    Args:
        path (str): Directory to read images from

    Returns:
        tuple: (PIL.Image object, full_path) or (None, None) if no images found
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}

    files = [
        os.path.join(path, f)
        for f in os.listdir(path)
        if os.path.splitext(f)[1].lower() in image_extensions
    ]

    if not files:
        return None, None

    full_path = random.choice(files)
    try:
        image = Image.open(full_path)
        copy = image.copy()
        image.close()
        return copy, full_path
    except Exception as e:
        print(f"⚠️ Failed to open {full_path}: {e}")
        return None, None


def correct_image_orientation(image: Image.Image, image_path: str) -> Image.Image:
    """
    Rotate the image according to its EXIF Orientation tag (if available).
    Uses piexif to support all EXIF-enabled images.
    """
    try:
        exif_dict = piexif.load(image_path)
        orientation = exif_dict.get("0th", {}).get(piexif.ImageIFD.Orientation, 1)

        if orientation == 1:
            return image
        elif orientation == 2:
            return image.transpose(Image.FLIP_LEFT_RIGHT)
        elif orientation == 3:
            return image.rotate(180, expand=True)
        elif orientation == 4:
            return image.transpose(Image.FLIP_TOP_BOTTOM)
        elif orientation == 5:
            return image.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
        elif orientation == 6:
            return image.rotate(270, expand=True)
        elif orientation == 7:
            return image.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True)
        elif orientation == 8:
            return image.rotate(90, expand=True)
        else:
            return image

    except Exception as e:
        logger.warning(f"Failed to correct orientation: {e}")
        return image


def add_metadata_overlay(img: Image.Image, image_path: str) -> Image.Image:
    """
    Reads EXIF date and GPS location from a PIL image,
    and draws it in the bottom-right corner with two lines:
    - Date on top
    - Address (from GPS) below
    """
    img = img.copy()
    draw = ImageDraw.Draw(img, 'RGBA')

    # --- Font setup ---
    try:
        font_date = ImageFont.truetype(
            os.path.join(FONTS_DIR, 'FunnelSans-VariableFont_wght.ttf'), 28
        )
        font_address = ImageFont.truetype(
            os.path.join(FONTS_DIR, 'FunnelSans-VariableFont_wght.ttf'), 24
        )
    except Exception:
        logger.error("Failed to load font, using system default")
        font_date = font_address = ImageFont.load_default()

    date_str = ""
    gps_str = ""

    # --- Extract EXIF ---
    try:
        exif_dict = piexif.load(image_path)

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
                gps_str = coords_to_address(lat_val, lon_val)  # your reverse geocoding function

    except Exception as e:
        logger.warning(f"Failed to read EXIF metadata: {e}")

    # --- Draw overlay if we have any text ---
    lines = []
    if date_str:
        lines.append(date_str)
    if gps_str:
        lines.append(gps_str)

    if not lines:
        return img

    # Measure text sizes
    padding = 10
    line_spacing = 6
    line_sizes = [
        draw.textbbox((0, 0), line, font=font_date if i == 0 else font_address)
        for i, line in enumerate(lines)
    ]
    widths = [bbox[2] - bbox[0] for bbox in line_sizes]
    heights = [bbox[3] - bbox[1] for bbox in line_sizes]

    box_width = max(widths) + 2 * padding
    box_height = sum(heights) + (len(lines) - 1) * line_spacing + 2 * padding

    # Position at bottom-right corner
    x0 = img.width - box_width - padding
    y0 = img.height - box_height - padding
    x1 = x0 + box_width
    y1 = y0 + box_height

    # Draw semi-transparent rectangle
    draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 255, 200))  # alpha=200

    # Draw text lines
    y_text = y0 + padding
    for i, line in enumerate(lines):
        font = font_date if i == 0 else font_address
        draw.text((x0 + padding, y_text), line, fill=(0, 0, 0), font=font)
        y_text += heights[i] + line_spacing

    return img
