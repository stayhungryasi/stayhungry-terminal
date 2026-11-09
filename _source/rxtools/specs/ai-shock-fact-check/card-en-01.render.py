#!/usr/bin/env python3
"""Render card-en-01 (es/ja) with img_render.py, but after the erase step restore the wafer area that the
English '?' overlapped from the clean Korean original (card-01.webp, same template)."""
import sys
import numpy as np
from PIL import Image

SRC = '/home/claude/stayhungry-terminal/_source'
sys.path.insert(0, SRC + '/rxtools')
import img_render as R

KO = np.array(Image.open(SRC + '/research/ai-shock-fact-check/card-01.webp').convert('RGB'))
PATCH = (455, 445, 610, 588)  # x0, y0, x1, y1
_erase = R.erase


def erase(a, r, pad=3):
    _erase(a, r, pad)
    x0, y0, x1, y1 = PATCH
    a[y0:y1, x0:x1] = KO[y0:y1, x0:x1]


R.erase = erase
R.render(SRC + '/rxtools/specs/ai-shock-fact-check/card-en-01.json')
