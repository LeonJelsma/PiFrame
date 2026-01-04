import numpy as np
from PIL import Image


def unique_palette_flat(palette_flat: tuple) -> tuple:
    cols = [tuple(palette_flat[i:i + 3]) for i in range(0, len(palette_flat), 3)]
    uniq = []
    for c in cols:
        if c not in uniq:
            uniq.append(c)
    return tuple(v for c in uniq for v in c)


def build_lut_5bit(palette_flat: tuple) -> tuple[np.ndarray, np.ndarray]:
    """
    Builds a 32x32x32 LUT mapping (r5,g5,b5) -> palette index,
    and returns (lut, palette_rgb_int16).

    lut shape: (32768,) uint8
    palette_rgb_int16: (K,3) int16
    """
    palette_flat = unique_palette_flat(palette_flat)
    pal = np.array([palette_flat[i:i + 3] for i in range(0, len(palette_flat), 3)], dtype=np.int16)
    k = pal.shape[0]

    # 5-bit grid values scaled to 0..255
    vals = np.linspace(0, 255, 32, dtype=np.float32)
    r, g, b = np.meshgrid(vals, vals, vals, indexing="ij")  # (32,32,32)
    grid = np.stack([r, g, b], axis=-1).reshape(-1, 3).astype(np.float32)  # (32768,3)

    # Compute nearest palette index for each grid point (vectorized)
    # dist^2 to each palette color
    d2 = np.empty((grid.shape[0], k), dtype=np.float32)
    for i in range(k):
        diff = grid - pal[i].astype(np.float32)
        d2[:, i] = np.sum(diff * diff, axis=1)
    lut = np.argmin(d2, axis=1).astype(np.uint8)  # (32768,)

    return lut, pal


def atkinson_dither_lut(
        img: Image.Image,
        palette_flat: tuple,
        lut: np.ndarray,
        palette_rgb: np.ndarray,
        *,
        serpentine: bool = True,
        # Neutral bias in RGB terms (cheap and effective)
        neutral_thresh: int = 10,  # channel spread threshold; higher => more neutral treated as B/W
        white_min: int = 240,  # near-white lock
        black_max: int = 35,  # near-black lock
        white_idx: int = 1,
        black_idx: int = 0,
) -> Image.Image:
    """
    Atkinson dithering using a 5-bit RGB LUT for nearest palette index.
    Returns P image with palette applied.
    """
    img = img.convert("RGB")
    src = np.asarray(img, dtype=np.uint8)
    h, w, _ = src.shape

    # int16 work buffer for error diffusion
    buf = src.astype(np.int16)
    out_idx = np.zeros((h, w), dtype=np.uint8)

    # Precompute padded palette for output image
    k = palette_rgb.shape[0]
    pal_padded = list(unique_palette_flat(palette_flat)) + [0, 0, 0] * (256 - k)

    for y in range(h):
        if serpentine and (y & 1):
            x_iter = range(w - 1, -1, -1)
            dir = -1
        else:
            x_iter = range(w)
            dir = 1

        for x in x_iter:
            r, g, b = buf[y, x]

            # clamp once
            if r < 0:
                r = 0
            elif r > 255:
                r = 255
            if g < 0:
                g = 0
            elif g > 255:
                g = 255
            if b < 0:
                b = 0
            elif b > 255:
                b = 255
            buf[y, x] = (r, g, b)

            # neutral bias
            spread = max(r, g, b) - min(r, g, b)
            if spread <= neutral_thresh:
                if r >= white_min and g >= white_min and b >= white_min:
                    idx = white_idx
                elif r <= black_max and g <= black_max and b <= black_max:
                    idx = black_idx
                else:
                    # LUT lookup (5-bit per channel)
                    idx = int(lut[((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3)])
            else:
                idx = int(lut[((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3)])

            out_idx[y, x] = idx
            pr, pg, pb = palette_rgb[idx]

            def div8_round(v: int) -> int:
                # round-to-nearest for /8, symmetric for negatives
                return (v + 4) // 8 if v >= 0 else -(((-v) + 4) // 8)

            er = div8_round(r - pr)
            eg = div8_round(g - pg)
            eb = div8_round(b - pb)

            x1 = x + dir
            x2 = x + 2 * dir
            y1 = y + 1
            y2 = y + 2

            # (x+1, y)
            if 0 <= x1 < w:
                buf[y, x1, 0] += er
                buf[y, x1, 1] += eg
                buf[y, x1, 2] += eb
            # (x+2, y)
            if 0 <= x2 < w:
                buf[y, x2, 0] += er
                buf[y, x2, 1] += eg
                buf[y, x2, 2] += eb

            if y1 < h:
                xm1 = x - dir
                # (x-1, y+1)
                if 0 <= xm1 < w:
                    buf[y1, xm1, 0] += er
                    buf[y1, xm1, 1] += eg
                    buf[y1, xm1, 2] += eb
                # (x, y+1)
                buf[y1, x, 0] += er
                buf[y1, x, 1] += eg
                buf[y1, x, 2] += eb
                # (x+1, y+1)
                if 0 <= x1 < w:
                    buf[y1, x1, 0] += er
                    buf[y1, x1, 1] += eg
                    buf[y1, x1, 2] += eb

            # (x, y+2)
            if y2 < h:
                buf[y2, x, 0] += er
                buf[y2, x, 1] += eg
                buf[y2, x, 2] += eb

    out = Image.fromarray(out_idx, mode="P")
    out.putpalette(pal_padded)
    return out
