#!/usr/bin/env python3
"""
Recolor a light (cream/white) research card into the hub's dark signature look, keeping accents and every graphic.

  python3 _source/rxtools/to_dark.py <in.webp> [<out.webp>]      (default: overwrite)

Neutral pixels (low chroma) get their lightness flipped onto the hub palette: cream background -> #0e1726,
white panels -> #15213b, light grey tracks -> deep slate, mid-grey bars -> slate, dark text -> near-white.
Coloured pixels (orange, green, yellow pills) keep their hue; dark coloured text is lifted so it stays readable on navy.
Works in OKLab so anti-aliased edges blend naturally.
"""
import sys
import numpy as np
from PIL import Image


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def to_oklab(rgb):
    r, g, b = [srgb_to_lin(rgb[..., i]) for i in range(3)]
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.stack([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s], -1)


def from_oklab(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return np.stack([lin_to_srgb(r), lin_to_srgb(g), lin_to_srgb(bb)], -1)


def hexlab(h):
    return to_oklab(np.array([[int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]]))[0]


# source lightness -> hub colour (neutrals). Order by source L.
ANCHORS = [(0.00, '#ffffff'), (0.25, '#eef2f8'), (0.45, '#c9d2e0'), (0.62, '#8e9bb2'), (0.78, '#46577a'),
           (0.90, '#24324f'), (0.945, '#1b2843'), (0.975, '#0e1726'), (0.99, '#132037'), (1.00, '#15213b')]


def recolor(rgb):
    lab = to_oklab(rgb)
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    C = np.hypot(a, b)
    xs = np.array([x for x, _ in ANCHORS])
    tl = np.array([hexlab(h) for _, h in ANCHORS])
    Ln = np.interp(L, xs, tl[:, 0]); an = np.interp(L, xs, tl[:, 1]); bn = np.interp(L, xs, tl[:, 2])
    k = np.clip((C - 0.05) / 0.08, 0, 1)                       # 0 = neutral, 1 = clearly coloured
    k = k * k * (3 - 2 * k)
    Lc = np.where(L < 0.6, 0.72, L)                             # dark coloured text: lifted to stay readable on navy
    out = np.stack([Ln * (1 - k) + Lc * k, an * (1 - k) + a, bn * (1 - k) + b], -1)
    return from_oklab(out)


if __name__ == '__main__':
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv) > 2 else src
    im = Image.open(src).convert('RGB')
    rgb = np.asarray(im).astype(np.float64) / 255
    res = (recolor(rgb) * 255 + 0.5).clip(0, 255).astype(np.uint8)
    Image.fromarray(res).save(dst, 'WEBP', quality=90, method=6)
    print('wrote', dst)
