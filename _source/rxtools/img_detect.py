#!/usr/bin/env python3
"""
Find the text lines in a research image so they can be translated.

  python3 _source/rxtools/img_detect.py <image> <outdir>

Writes into <outdir>:
  <name>.boxes.json   [{"i", "rect":[x0,y0,x1,y1], "ocr", "bg":"#rrggbb", "fg":"#rrggbb", "h"}]
  <name>.boxes.png    the image with every box drawn and numbered (look at it with an image viewer)
  <name>.boxes-top.png / -bottom.png   the same, cropped in halves and enlarged, for small labels

OCR text is only a hint (Korean OCR is rough); the boxes are what matter. Text the detector misses can be
added to a spec by hand as "rect". Needs tesseract + kor.traineddata (TESSDATA_PREFIX, default /home/claude/tessdata).
"""
import csv, io, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont

TESS = os.environ.get('TESSDATA_PREFIX', '/home/claude/tessdata')
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'


def hexc(c):
    return '#%02x%02x%02x' % tuple(int(v) for v in c[:3])


def colors(a, r):
    x0, y0, x1, y1 = r
    H, W = a.shape[:2]
    ring = np.concatenate([a[max(0, y0 - 4):y0, x0:x1].reshape(-1, 3), a[y1:min(H, y1 + 4), x0:x1].reshape(-1, 3),
                           a[y0:y1, max(0, x0 - 4):x0].reshape(-1, 3), a[y0:y1, x1:min(W, x1 + 4)].reshape(-1, 3)])
    bg = np.median(ring, axis=0) if len(ring) else np.median(a[y0:y1, x0:x1].reshape(-1, 3), axis=0)
    inner = a[y0:y1, x0:x1].reshape(-1, 3).astype(float)
    d = np.linalg.norm(inner - bg, axis=1)
    fg = np.median(inner[d >= np.percentile(d, 90)], axis=0) if len(inner) else bg
    return bg, fg


def detect(path):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    k = 2 if max(W, H) < 2200 else 1
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
    im.resize((W * k, H * k), Image.LANCZOS).save(tmp)
    out = []
    for psm in ('11', '3'):
        r = subprocess.run(['tesseract', tmp, '-', '-l', 'kor+eng', '--psm', psm, '-c', 'tessedit_create_tsv=1'],
                           capture_output=True, text=True, env={'TESSDATA_PREFIX': TESS, 'PATH': '/usr/bin:/bin'})
        lines = {}
        for x in csv.DictReader(io.StringIO(r.stdout), delimiter='\t', quoting=csv.QUOTE_NONE):
            if x.get('level') != '5' or not (x.get('text') or '').strip():
                continue
            key = (x['block_num'], x['par_num'], x['line_num'])
            b = [int(x['left']) // k, int(x['top']) // k, (int(x['left']) + int(x['width'])) // k, (int(x['top']) + int(x['height'])) // k]
            L = lines.setdefault(key, {'rect': b[:], 'ocr': []})
            L['rect'] = [min(L['rect'][0], b[0]), min(L['rect'][1], b[1]), max(L['rect'][2], b[2]), max(L['rect'][3], b[3])]
            L['ocr'].append(x['text'])
        out.append(list(lines.values()))
    os.unlink(tmp)
    # merge the two passes: keep sparse-mode lines, add auto-mode lines that cover new ground
    base = out[0]
    def ov(a, b):
        ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
        return ix * iy / max(1, (a[2] - a[0]) * (a[3] - a[1]))
    for L in out[1]:
        if all(ov(L['rect'], B['rect']) < .3 for B in base):
            base.append(L)
    base = [L for L in base if (L['rect'][2] - L['rect'][0]) > 4 and (L['rect'][3] - L['rect'][1]) > 5]
    base.sort(key=lambda L: (L['rect'][1] // 8, L['rect'][0]))
    a = np.asarray(im)
    res = []
    for i, L in enumerate(base):
        bg, fg = colors(a, L['rect'])
        res.append({'i': i, 'rect': L['rect'], 'ocr': ' '.join(L['ocr']), 'bg': hexc(bg), 'fg': hexc(fg), 'h': L['rect'][3] - L['rect'][1]})
    return im, res


def annotate(im, res):
    a = im.copy()
    d = ImageDraw.Draw(a)
    f = ImageFont.truetype(FONT, 14, index=1)
    for b in res:
        d.rectangle(b['rect'], outline=(0, 255, 90), width=2)
        tx, ty = b['rect'][0], max(0, b['rect'][1] - 16)
        d.rectangle([tx, ty, tx + 8 + 8 * len(str(b['i'])), ty + 16], fill=(0, 0, 0))
        d.text((tx + 3, ty), str(b['i']), fill=(0, 255, 255), font=f)
    return a


if __name__ == '__main__':
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    name = os.path.splitext(os.path.basename(src))[0]
    im, res = detect(src)
    json.dump(res, open(os.path.join(outdir, name + '.boxes.json'), 'w'), ensure_ascii=False, indent=0)
    an = annotate(im, res)
    an.save(os.path.join(outdir, name + '.boxes.png'))
    W, H = an.size
    an.crop((0, 0, W, H // 2 + 20)).resize((W * 3 // 2, (H // 2 + 20) * 3 // 2)).save(os.path.join(outdir, name + '.boxes-top.png'))
    an.crop((0, H // 2 - 20, W, H)).resize((W * 3 // 2, (H - H // 2 + 20) * 3 // 2)).save(os.path.join(outdir, name + '.boxes-bottom.png'))
    for b in res:
        print(b['i'], b['rect'], b['h'], b['bg'], b['fg'], b['ocr'])
