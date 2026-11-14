#!/usr/bin/env python3
"""Link-preview images for research reports: og.jpg (+ og.en/es/ja.jpg) 1200x630 from the first card, on the hub navy.

  python3 _source/rxtools/og.py [slug ...]        (default: every report that has card-01.webp)

research.py adds og:image / twitter:image when the file exists. Re-run after a cover card changes.
"""
import os, sys
from PIL import Image

R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'research')
for slug in sys.argv[1:] or sorted(os.listdir(R)):
    d = os.path.join(R, slug)
    for sfx in ('', '.en', '.es', '.ja'):
        src = next((p for p in (os.path.join(d, f'card-01{sfx}.webp'), os.path.join(d, 'card-en-01.webp') if sfx == '.en' else '',
                                os.path.join(d, f'card-en-01{sfx}.webp')) if p and os.path.exists(p)), None)
        if not src:
            continue
        im = Image.open(src).convert('RGB')
        bg = Image.new('RGB', (1200, 630), im.getpixel((4, 4)))
        h = 630; w = round(im.width * h / im.height)
        bg.paste(im.resize((w, h), Image.LANCZOS), ((1200 - w) // 2, 0))
        bg.save(os.path.join(d, f'og{sfx}.jpg'), 'JPEG', quality=88, optimize=True)
        print('wrote', slug, f'og{sfx}.jpg')
