import os

from PIL import Image, ImageEnhance, ImageOps

from const import DISPLAY_HEIGHT, DISPLAY_WIDTH


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

def apply_exif_orientation(img: Image.Image) -> Image.Image:
    """
    Apply orientation from EXIF metadata to the pixel data,
    then strip the original tag to avoid double-rotation.
    """
    return ImageOps.exif_transpose(img)