from __future__ import annotations

from functools import lru_cache

import atkinson_rs
import numpy as np
from PIL import Image


def _unique_palette_flat(palette_flat: tuple[int, ...]) -> tuple[int, ...]:
    cols = [tuple(palette_flat[i:i + 3]) for i in range(0, len(palette_flat), 3)]
    uniq = []
    for c in cols:
        if c not in uniq:
            uniq.append(c)
    return tuple(v for c in uniq for v in c)


def _palette_rgb_from_flat(palette_flat: tuple[int, ...]) -> np.ndarray:
    palette_flat = _unique_palette_flat(palette_flat)
    return np.array([palette_flat[i:i + 3] for i in range(0, len(palette_flat), 3)], dtype=np.uint8)


@lru_cache(maxsize=16)
def _lut_and_palette_bytes(palette_flat: tuple[int, ...]) -> tuple[bytes, bytes, int]:
    """
    Returns (lut_bytes, palette_bytes, k) for a given palette_flat.
    Cached so it's built once per palette.
    """
    palette_rgb = _palette_rgb_from_flat(palette_flat)  # (K,3) uint8
    k = int(palette_rgb.shape[0])

    # Build 5-bit LUT: 32*32*32 = 32768 entries
    vals = np.linspace(0, 255, 32, dtype=np.float32)
    r, g, b = np.meshgrid(vals, vals, vals, indexing="ij")
    grid = np.stack([r, g, b], axis=-1).reshape(-1, 3).astype(np.float32)  # (32768,3)

    pal = palette_rgb.astype(np.float32)
    d2 = np.empty((grid.shape[0], k), dtype=np.float32)
    for i in range(k):
        diff = grid - pal[i]
        d2[:, i] = np.sum(diff * diff, axis=1)

    lut = np.argmin(d2, axis=1).astype(np.uint8)  # (32768,)
    return lut.tobytes(), palette_rgb.tobytes(), k


def atkinson_dither(
        img: Image.Image,
        palette_flat: tuple[int, ...],
        *,
        serpentine: bool = True,
) -> Image.Image:
    """
    Dither a PIL image to the given palette using Rust Atkinson + 5-bit LUT.
    You only pass (image, palette_flat). Everything else is internal/cached.

    Returns a P-mode image with the palette attached.
    """
    img = img.convert("RGB")
    arr = np.asarray(img, dtype=np.uint8)
    h, w, _ = arr.shape

    lut_bytes, pal_bytes, k = _lut_and_palette_bytes(tuple(palette_flat))

    idx_bytes = atkinson_rs.atkinson_lut(
        arr.tobytes(),
        w,
        h,
        lut_bytes,
        pal_bytes,
        serpentine,
    )

    idx = np.frombuffer(idx_bytes, dtype=np.uint8).reshape((h, w))
    out = Image.fromarray(idx, mode="P")

    # Attach palette for preview/export (pad to 256 colors)
    pal_u8 = np.frombuffer(pal_bytes, dtype=np.uint8)
    pal_list = pal_u8.tolist() + [0, 0, 0] * (256 - k)
    out.putpalette(pal_list)

    return out
