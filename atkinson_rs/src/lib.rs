use pyo3::prelude::*;
use pyo3::types::PyBytes;

#[inline(always)]
fn clamp_u8(v: i16) -> u8 {
    if v < 0 { 0 } else if v > 255 { 255 } else { v as u8 }
}

#[inline(always)]
fn div8_round(v: i16) -> i16 {
    if v >= 0 { (v + 4) / 8 } else { -((-v + 4) / 8) }
}

#[inline(always)]
fn lut_index_5bit(r: u8, g: u8, b: u8) -> usize {
    (((r as usize) >> 3) << 10) | (((g as usize) >> 3) << 5) | ((b as usize) >> 3)
}

#[pyfunction]
fn atkinson_lut<'py>(
    py: Python<'py>,
    rgb: &Bound<'py, PyBytes>,      // bytes length = width*height*3
    width: usize,
    height: usize,
    lut: &Bound<'py, PyBytes>,      // bytes length = 32768 (5-bit LUT)
    palette: &Bound<'py, PyBytes>,  // bytes length = K*3
    serpentine: bool,
) -> PyResult<Bound<'py, PyBytes>> {
    let rgb_buf = rgb.as_bytes();
    let lut_buf = lut.as_bytes();
    let pal_buf = palette.as_bytes();

    if rgb_buf.len() != width * height * 3 {
        return Err(pyo3::exceptions::PyValueError::new_err("rgb buffer has wrong length"));
    }
    if lut_buf.len() != 32768 {
        return Err(pyo3::exceptions::PyValueError::new_err("lut must have length 32768 for 5-bit LUT"));
    }
    if pal_buf.len() % 3 != 0 || pal_buf.is_empty() {
        return Err(pyo3::exceptions::PyValueError::new_err("palette length must be K*3 with K>=1"));
    }
    let k = pal_buf.len() / 3;

    // Palette i16
    let mut pal_i16: Vec<i16> = Vec::with_capacity(pal_buf.len());
    pal_i16.extend(pal_buf.iter().map(|&v| v as i16));

    // Work buffer i16 RGB
    let mut buf: Vec<i16> = Vec::with_capacity(rgb_buf.len());
    buf.extend(rgb_buf.iter().map(|&v| v as i16));

    let mut out: Vec<u8> = vec![0u8; width * height];

    for y in 0..height {
        let odd = (y & 1) == 1;
        let (x_start, x_end, dir): (isize, isize, isize) = if serpentine && odd {
            (width as isize - 1, -1, -1)
        } else {
            (0, width as isize, 1)
        };

        let mut x = x_start;
        while x != x_end {
            let xi = x as usize;
            let pix = (y * width + xi) * 3;

            // clamp pixel
            let r = clamp_u8(buf[pix]);
            let g = clamp_u8(buf[pix + 1]);
            let b = clamp_u8(buf[pix + 2]);

            buf[pix] = r as i16;
            buf[pix + 1] = g as i16;
            buf[pix + 2] = b as i16;

            // LUT -> palette index
            let li = lut_index_5bit(r, g, b);
            let idx = lut_buf[li] as usize;
            if idx >= k {
                return Err(pyo3::exceptions::PyValueError::new_err("lut index out of palette bounds"));
            }
            out[y * width + xi] = idx as u8;

            // chosen palette color
            let pr = pal_i16[idx * 3];
            let pg = pal_i16[idx * 3 + 1];
            let pb = pal_i16[idx * 3 + 2];

            // error /8 rounded
            let er = div8_round(r as i16 - pr);
            let eg = div8_round(g as i16 - pg);
            let eb = div8_round(b as i16 - pb);

            let x1 = x + dir;
            let x2 = x + 2 * dir;
            let y1 = y + 1;
            let y2 = y + 2;

            // (x+1, y)
            if x1 >= 0 && (x1 as usize) < width {
                let p = (y * width + x1 as usize) * 3;
                buf[p] += er; buf[p + 1] += eg; buf[p + 2] += eb;
            }
            // (x+2, y)
            if x2 >= 0 && (x2 as usize) < width {
                let p = (y * width + x2 as usize) * 3;
                buf[p] += er; buf[p + 1] += eg; buf[p + 2] += eb;
            }

            // next row
            if y1 < height {
                // (x-1, y+1)
                let xm1 = x - dir;
                if xm1 >= 0 && (xm1 as usize) < width {
                    let p = (y1 * width + xm1 as usize) * 3;
                    buf[p] += er; buf[p + 1] += eg; buf[p + 2] += eb;
                }
                // (x, y+1)
                {
                    let p = (y1 * width + xi) * 3;
                    buf[p] += er; buf[p + 1] += eg; buf[p + 2] += eb;
                }
                // (x+1, y+1)
                if x1 >= 0 && (x1 as usize) < width {
                    let p = (y1 * width + x1 as usize) * 3;
                    buf[p] += er; buf[p + 1] += eg; buf[p + 2] += eb;
                }
            }

            // (x, y+2)
            if y2 < height {
                let p = (y2 * width + xi) * 3;
                buf[p] += er; buf[p + 1] += eg; buf[p + 2] += eb;
            }

            x += dir;
        }
    }

    Ok(PyBytes::new(py, &out))
}

#[pymodule]
fn atkinson_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(atkinson_lut, m)?)?;
    Ok(())
}
