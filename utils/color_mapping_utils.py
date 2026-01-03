import numpy as np
from PIL import Image
from skimage.color import rgb2lab

def _palette_rgb_to_lab(palette_rgb: np.ndarray) -> np.ndarray:
    """
    palette_rgb: (K,3) uint8
    returns: (K,3) float32 in Lab
    """
    pal = (palette_rgb.astype(np.float32) / 255.0)[None, :, :]  # (1,K,3)
    pal_lab = rgb2lab(pal).astype(np.float32)[0]                # (K,3)
    return pal_lab

def quantize_lab_nearest(img_rgb: Image.Image, palette_flat: tuple) -> Image.Image:
    """
    Returns a P-mode image whose pixels are indices into the provided palette,
    chosen by nearest color in Lab (perceptual).
    """
    rgb = np.array(img_rgb.convert("RGB"), dtype=np.uint8)          # (H,W,3)
    h, w, _ = rgb.shape

    # Build palette arrays
    palette_rgb = np.array([palette_flat[i:i+3] for i in range(0, len(palette_flat), 3)], dtype=np.uint8)
    k = palette_rgb.shape[0]
    pal_lab = _palette_rgb_to_lab(palette_rgb)

    # Convert image to Lab in one vectorized shot
    lab = rgb2lab(rgb.astype(np.float32) / 255.0).astype(np.float32)  # (H,W,3)

    # Compute nearest palette index (vectorized)
    # dist^2 = sum((lab - pal_lab)^2) over channels
    # result: (H,W)
    d2 = np.empty((h, w, k), dtype=np.float32)
    for i in range(k):
        dl = lab[:, :, 0] - pal_lab[i, 0]
        da = lab[:, :, 1] - pal_lab[i, 1]
        db = lab[:, :, 2] - pal_lab[i, 2]
        d2[:, :, i] = dl*dl + da*da + db*db

    idx = np.argmin(d2, axis=2).astype(np.uint8)  # (H,W)

    out = Image.fromarray(idx, mode="P")
    # putpalette expects 768-length, so pad
    pal_padded = list(palette_flat) + [0, 0, 0] * (256 - k)
    out.putpalette(pal_padded)
    return out
