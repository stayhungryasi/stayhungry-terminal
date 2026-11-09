#!/usr/bin/env python3
"""
Redraw a research image in another language: erase the Korean text lines, draw the translation in their place.

  python3 _source/rxtools/img_render.py <spec.json> [en es ja]

Spec (kept in _source/rxtools/specs/<slug>/<name>.json, next to the <name>.boxes.json from img_detect.py):
{
  "slug": "railroad-vs-semis-130y",
  "src": "card-04.webp",                     # the Korean original in _source/research/<slug>/
  "boxes": "card-04.boxes.json",             # from img_detect.py, same folder as the spec
  "langs": ["en", "es", "ja"],               # what to write; output is <name>.<lang>.webp next to the original
  "erase": [[x0, y0, x1, y1]],               # optional: more areas to wipe in every language (stray Korean)
  "keep": [[x0, y0, x1, y1]],                # optional: areas restored from the original after erasing (swatches, bars)
  "regions": [
    {"boxes": [0], "text": {"en": "03 Parallel history", "es": "...", "ja": "..."},
     "weight": "bold",           # light | regular | medium | bold | black      (default regular)
     "align": "left",            # left | center | right                         (default left)
     "valign": "top",            # top | middle | bottom                         (default top)
     "size": null,               # font px; default = estimated from the original line height
     "lh": null,                 # line pitch px; default = original pitch (or 1.4 x size)
     "color": null,              # default = sampled from the original text
     "accent": "#F2545B",        # colour for ==marked== words; **double stars** = one weight heavier
     "expand": [0, 0, 0, 0],     # grow the drawing box left, top, right, bottom (px) if a language runs long
     "nowrap": false,            # keep on one line, shrink to fit instead
     "minscale": 0.6,            # smallest size as a share of the estimate before it warns
     "rect": [x0, y0, x1, y1]    # instead of "boxes", for text the detector missed
    }
  ]
}
Text may contain \\n for a forced line break. Prints a WARNING when a region could not fit; widen it with "expand".
"""
import json, os, re, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.join(os.path.dirname(HERE), 'research')
FD = '/usr/share/fonts/opentype/noto/'
WEIGHTS = ['light', 'regular', 'medium', 'bold', 'black']
WFILE = {'light': 'NotoSansCJK-Light.ttc', 'regular': 'NotoSansCJK-Regular.ttc', 'medium': 'NotoSansCJK-Medium.ttc',
         'bold': 'NotoSansCJK-Bold.ttc', 'black': 'NotoSansCJK-Black.ttc'}
_fc = {}


def font(weight, size, lang):
    k = (weight, int(size), lang)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FD + WFILE[weight], max(6, int(round(size))), index=0 if lang == 'ja' else 1)
    return _fc[k]


# glyph metrics of Hangul at 100px: box height and how far its top sits above the baseline
_ref = ImageFont.truetype(FD + WFILE['regular'], 100, index=1).getbbox('가한글다', anchor='ls')
K_H = (_ref[3] - _ref[1]) / 100.0
K_TOP = -_ref[1] / 100.0


def hx(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def erase(a, r, pad=3):
    H, W = a.shape[:2]
    x0, y0, x1, y1 = max(0, r[0] - pad), max(0, r[1] - pad), min(W, r[2] + pad), min(H, r[3] + pad)
    ring = np.concatenate([a[max(0, y0 - 3):y0, x0:x1].reshape(-1, 3), a[y1:min(H, y1 + 3), x0:x1].reshape(-1, 3),
                           a[y0:y1, max(0, x0 - 3):x0].reshape(-1, 3), a[y0:y1, x1:min(W, x1 + 3)].reshape(-1, 3)]).astype(float)
    if not len(ring):
        return
    bg = np.median(ring, axis=0)
    if ring.std(axis=0).max() < 9:
        a[y0:y1, x0:x1] = bg.astype(np.uint8)
        return
    sub = a[y0:y1, x0:x1].astype(float)
    m = (np.linalg.norm(sub - bg, axis=2) > 38).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
    full = np.zeros(a.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = m
    a[:] = cv2.inpaint(a, full, 5, cv2.INPAINT_TELEA)


def tight(a, r, thr=42):
    """Shrink a detector box to the pixels that actually differ from the background."""
    H, W = a.shape[:2]
    x0, y0, x1, y1 = max(0, r[0]), max(0, r[1]), min(W, r[2]), min(H, r[3])
    if x1 <= x0 or y1 <= y0:
        return list(r)
    sub = a[y0:y1, x0:x1].astype(float)
    edge = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]])
    bg = np.median(edge, axis=0)
    m = np.linalg.norm(sub - bg, axis=2) > thr
    ys, xs = np.where(m)
    if not len(ys):
        return list(r)
    return [x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1]


def lines_of(rects):
    rs = sorted(rects, key=lambda r: r[1])
    out = []
    for r in rs:
        for L in out:
            if min(L[3], r[3]) - max(L[1], r[1]) > .4 * min(L[3] - L[1], r[3] - r[1]):
                L[:] = [min(L[0], r[0]), min(L[1], r[1]), max(L[2], r[2]), max(L[3], r[3])]
                break
        else:
            out.append(list(r))
    return sorted(out, key=lambda L: L[1])


def runs(text):
    """'a **b** ==c==' -> [(chunk, heavy, accent)]"""
    out, heavy, acc = [], False, False
    for part in re.split(r'(\*\*|==)', text):
        if part == '**':
            heavy = not heavy
        elif part == '==':
            acc = not acc
        elif part:
            out.append((part, heavy, acc))
    return out


NO_START = set('、。,.)）」』】〕・ー!?！？%:;')


def tokens(text, lang):
    toks = []
    for chunk, heavy, acc in runs(text):
        if lang == 'ja':
            for m in re.finditer(r'\n|[A-Za-z0-9$%+\-.,/:~()]+ ?|\s|.', chunk):
                toks.append((m.group(0), heavy, acc))
        else:
            for m in re.finditer(r'\n|\S+[^\S\n]*|[^\S\n]+', chunk):
                toks.append((m.group(0), heavy, acc))
    return toks


def layout(text, lang, weight, size, maxw, nowrap):
    wi = WEIGHTS.index(weight)
    heavyw = WEIGHTS[min(len(WEIGHTS) - 1, wi + 1)]
    lines, cur, curw = [], [], 0.0
    for t, heavy, acc in tokens(text, lang):
        if t == '\n':
            lines.append(cur); cur, curw = [], 0.0; continue
        f = font(heavyw if heavy else weight, size, lang)
        w = f.getlength(t)
        if cur and not nowrap and curw + f.getlength(t.rstrip()) > maxw and not (lang == 'ja' and t[0] in NO_START):
            lines.append(cur); cur, curw = [], 0.0
            if t.isspace():
                continue
            t = t.lstrip(); w = f.getlength(t)
        cur.append((t, f, acc)); curw += w
    lines.append(cur)
    widths = [sum(f.getlength(t) for t, f, a in L) - (L[-1][1].getlength(L[-1][0]) - L[-1][1].getlength(L[-1][0].rstrip()) if L else 0) for L in lines]
    return lines, widths


def render(spec_path, langs=None):
    sd = os.path.dirname(os.path.abspath(spec_path))
    spec = json.load(open(spec_path, encoding='utf-8'))
    rdir = os.path.join(RESEARCH, spec['slug'])
    src = os.path.join(rdir, spec['src'])
    boxes = {b['i']: b for b in json.load(open(os.path.join(sd, spec['boxes'])))} if spec.get('boxes') else {}
    name = os.path.splitext(spec['src'])[0]
    warns = []
    for lang in (langs or spec.get('langs') or ['en', 'es', 'ja']):
        a = np.array(Image.open(src).convert('RGB'))
        regs = []
        for ri, R in enumerate(spec['regions']):
            raw = [boxes[i]['rect'] for i in R.get('boxes', [])]
            rects = [tight(a, r) for r in raw] + ([R['rect']] if R.get('rect') else [])
            if not rects:
                continue
            fg = R.get('color') or next((boxes[i]['fg'] for i in R.get('boxes', [])), None)
            regs.append((ri, R, rects, fg))
        if not regs and not spec.get('erase'):
            continue
        orig = a.copy()
        for ri, R, rects, fg in regs:
            for r in lines_of(rects):          # whole line, so gaps between OCR fragments go too
                erase(a, r, R.get('pad', 3))
        for r in spec.get('erase', []):
            erase(a, r)
        for r in spec.get('keep', []):         # put back graphics (legend swatches, bars) an erase touched
            a[r[1]:r[3], r[0]:r[2]] = orig[r[1]:r[3], r[0]:r[2]]
        im = Image.fromarray(a)
        d = ImageDraw.Draw(im)
        for ri, R, rects, fg in regs:
            txt = (R.get('text') or {}).get(lang)
            if txt is None:
                warns.append(f'{lang} region {ri}: no text'); continue
            if txt == '':
                continue
            if not fg:
                x0, y0, x1, y1 = rects[0]
                sub = orig[y0:y1, x0:x1].reshape(-1, 3).astype(float)
                bg = np.median(sub, axis=0); dd = np.linalg.norm(sub - bg, axis=1)
                fg = '#%02x%02x%02x' % tuple(int(v) for v in np.median(sub[dd >= np.percentile(dd, 90)], axis=0))
            L = lines_of(rects)
            ex = R.get('expand', [0, 0, 0, 0])
            ux0, uy0 = min(r[0] for r in L) - ex[0], min(r[1] for r in L) - ex[1]
            ux1, uy1 = max(r[2] for r in L) + ex[2], max(r[3] for r in L) + ex[3]
            hline = float(np.median([r[3] - r[1] for r in L]))
            est = R.get('size') or hline / K_H
            pitch0 = R.get('lh') or (float(np.median(np.diff([r[1] for r in L]))) if len(L) > 1 else est * 1.42)
            weight = R.get('weight', 'regular')
            maxw, maxh = ux1 - ux0, uy1 - uy0
            s, fit = est, False
            while s >= est * R.get('minscale', 0.6) - 1e-6:
                lh = pitch0 * s / est
                lines, widths = layout(txt, lang, weight, s, maxw, R.get('nowrap'))
                blockh = (len(lines) - 1) * lh + s * K_H
                if max(widths or [0]) <= maxw + 1 and blockh <= maxh + s * .3:
                    fit = True; break
                s *= .96
            if not fit:
                warns.append(f'{lang} region {ri} ({txt[:40]!r}) does not fit at {R.get("minscale", 0.6):.0%} size: widen with "expand"')
            lh = pitch0 * s / est
            blockh = (len(lines) - 1) * lh + s * K_H
            va = R.get('valign', 'top')
            top = uy0 if va == 'top' else (uy1 - blockh if va == 'bottom' else (uy0 + uy1 - blockh) / 2)
            col, acc = hx(fg), hx(R['accent']) if R.get('accent') else hx(fg)
            for li, (line, w) in enumerate(zip(lines, widths)):
                al = R.get('align', 'left')
                x = ux0 if al == 'left' else (ux1 - w if al == 'right' else (ux0 + ux1 - w) / 2)
                base = top + li * lh + K_TOP * s
                for t, f, isacc in line:
                    d.text((x, base), t, font=f, fill=acc if isacc else col, anchor='ls')
                    x += f.getlength(t)
        out = os.path.join(rdir, f'{name}.{lang}.webp')
        im.save(out, 'WEBP', quality=90, method=6)
        print('wrote', os.path.relpath(out, RESEARCH))
    for w in warns:
        print('WARNING', w)
    return warns


if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2:] or None)
