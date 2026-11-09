#!/usr/bin/env python3
"""Redraw strike-through lines on rendered cards.
usage: strike.py <out.webp> <bg-hex> <y0>,<y1>,<x0>,<x1>,<liney>,<thick>,<hex> ...
Finds the x-extent of text in band [y0,y1) starting at x0 (scan up to x1) and draws the line."""
import sys
import numpy as np
from PIL import Image

path, bg = sys.argv[1], sys.argv[2]
bgc = np.array([int(bg.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)])
a = np.array(Image.open(path).convert('RGB'))
for spec in sys.argv[3:]:
    y0, y1, x0, x1, ly, th, col = spec.split(',')
    y0, y1, x0, x1, ly, th = map(int, (y0, y1, x0, x1, ly, th))
    sub = a[y0:y1, x0:x1].astype(int)
    m = np.linalg.norm(sub - bgc, axis=2) > 50
    xs = np.where(m.any(0))[0]
    if not len(xs):
        print('no text in', spec); continue
    lx0, lx1 = x0 + xs.min(), x0 + xs.max() + 1
    c = [int(col.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)]
    a[ly:ly + th, lx0:lx1] = c
    print(path.split('/')[-1], 'strike', lx0, lx1, 'y', ly)
Image.fromarray(a).save(path, 'WEBP', quality=90, method=6)
