import numpy as np
from PIL import Image
from skimage.color import rgb2lab

BLACK_IDX = 0
WHITE_IDX = 1


def _flat_palette_to_rgb(palette_flat: tuple) -> np.ndarray:
    return np.array([palette_flat[i:i + 3] for i in range(0, len(palette_flat), 3)], dtype=np.uint8)


def _palette_rgb_to_lab(palette_rgb_u8: np.ndarray) -> np.ndarray:
    pal = (palette_rgb_u8.astype(np.float32) / 255.0)[None, :, :]  # (1,K,3)
    return rgb2lab(pal).astype(np.float32)[0]  # (K,3)


def atkinson_dither_lab(
        img_rgb: Image.Image,
        palette_flat: tuple,
        *,
        neutral_chroma: float = 10.0,  # higher = treat more pixels as neutral-ish
        white_L: float = 92.0,  # bright neutrals -> white
        black_L: float = 18.0,  # dark neutrals -> black
        serpentine: bool = True,
) -> Image.Image:
    """
    Atkinson error-diffusion dithering performed in Lab space, selecting nearest palette color in Lab.
    Returns a P-mode image of palette indices (compatible with putpalette/replace_colors).
    """

    palette_rgb = _flat_palette_to_rgb(palette_flat)
    k = palette_rgb.shape[0]
    palette_lab = _palette_rgb_to_lab(palette_rgb)

    # Image -> Lab float32
    rgb = np.array(img_rgb.convert("RGB"), dtype=np.uint8)
    h, w, _ = rgb.shape
    lab = rgb2lab(rgb.astype(np.float32) / 255.0).astype(np.float32)  # (H,W,3)

    # Output indices
    out_idx = np.zeros((h, w), dtype=np.uint8)

    # Atkinson distributes 1/8 error to 6 neighbors:
    # (x+1,y), (x+2,y), (x-1,y+1), (x,y+1), (x+1,y+1), (x,y+2)
    # We'll implement serpentine scanning to reduce directional artifacts.

    for y in range(h):
        if serpentine and (y % 2 == 1):
            x_range = range(w - 1, -1, -1)
            dir = -1
        else:
            x_range = range(w)
            dir = 1

        for x in x_range:
            L, a, b = lab[y, x]
            C = (a * a + b * b) ** 0.5

            # Neutral bias: steer bright neutrals to white, dark neutrals to black
            if C < neutral_chroma:
                if L >= white_L:
                    idx = WHITE_IDX
                    chosen = palette_lab[idx]
                elif L <= black_L:
                    idx = BLACK_IDX
                    chosen = palette_lab[idx]
                else:
                    # normal nearest for mid neutrals
                    dif = palette_lab - lab[y, x]
                    d2 = np.sum(dif * dif, axis=1)
                    idx = int(np.argmin(d2))
                    chosen = palette_lab[idx]
            else:
                dif = palette_lab - lab[y, x]
                d2 = np.sum(dif * dif, axis=1)
                idx = int(np.argmin(d2))
                chosen = palette_lab[idx]

            out_idx[y, x] = idx

            # Error in Lab
            err = lab[y, x] - chosen
            err *= (1.0 / 8.0)

            # distribute error
            # current row
            x1 = x + dir
            x2 = x + 2 * dir
            if 0 <= x1 < w:
                lab[y, x1] += err
            if 0 <= x2 < w:
                lab[y, x2] += err

            # next row
            y1 = y + 1
            if y1 < h:
                xm1 = x - dir
                if 0 <= xm1 < w:
                    lab[y1, xm1] += err
                lab[y1, x] += err
                if 0 <= x1 < w:
                    lab[y1, x1] += err

            # row after next
            y2 = y + 2
            if y2 < h:
                lab[y2, x] += err

    out = Image.fromarray(out_idx, mode="P")
    pal_padded = list(palette_flat) + [0, 0, 0] * (256 - k)
    out.putpalette(pal_padded)
    return out
