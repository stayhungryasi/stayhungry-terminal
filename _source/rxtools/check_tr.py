#!/usr/bin/env python3
"""
Check a translated research body against its Korean original.

  python3 _source/rxtools/check_tr.py <slug> <lang>        (lang: en | es | ja)

Compares _source/research/<slug>/body.html (or app.html) with body.<lang>.html (app.<lang>.html):
  STRUCTURE  same count of block tags (h2 h3 p li table tr th td figure svg img a ...) and same link targets
  HANGUL     Korean text left in visible text or in alt/title/aria-label/placeholder attributes
  NUMBERS    numbers in the original that are missing in the translation, and new ones (review each one:
             unit conversions like 2.3조 -> 2.3 trillion keep the digits; 2만 -> 20,000 does not)
  IMAGES     <img src> that do not exist, or still point at a Korean image when a <name>.<lang>.webp exists
  RULE       publishing-rule words (same list as research.py)
Exit code 1 when STRUCTURE, HANGUL, IMAGES or RULE fail. NUMBERS is a list to review, not a gate.
"""
import collections, html, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(os.path.dirname(HERE), 'research')
sys.path.insert(0, os.path.dirname(HERE))
from research import FORBIDDEN  # noqa: E402

BLOCK = ['h1', 'h2', 'h3', 'h4', 'p', 'li', 'ul', 'ol', 'table', 'tr', 'th', 'td', 'figure', 'figcaption', 'svg', 'img', 'a', 'blockquote', 'section', 'details', 'summary', 'button', 'script', 'canvas', 'select', 'option', 'input']
HANGUL = re.compile(r'[가-힣ㄱ-ㆎ]')
NUM = re.compile(r'(?<![A-Za-z0-9_.,])[-+−]?\$?\d[\d,]*(?:\.\d+)?%?')  # ASCII-only lookbehind: 約722億 / 2026年 count in Japanese


def visible(h):
    h = re.sub(r'<script\b.*?</script>|<style\b.*?</style>', ' ', h, flags=re.S | re.I)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', h))
    return re.sub(r'\s+', ' ', t)


def attrs(h):
    return [html.unescape(m.group(2)) for m in re.finditer(r'\b(alt|title|aria-label|placeholder|data-tip|data-label)="([^"]*)"', h)]


def scripts(h):
    return ' '.join(re.findall(r'<script\b[^>]*>(.*?)</script>', h, flags=re.S | re.I))


def nums(t):
    out = []
    for m in NUM.finditer(t):
        v = m.group(0).replace(',', '').replace('−', '-').replace('$', '').lstrip('+')
        if re.fullmatch(r'-?\d+(\.\d+)?%?', v):
            out.append(v)
    return collections.Counter(out)


def main(slug, lang):
    d = os.path.join(R, slug)
    kind = 'app' if os.path.exists(os.path.join(d, 'app.html')) else 'body'
    ko = open(os.path.join(d, f'{kind}.html'), encoding='utf-8').read()
    p = os.path.join(d, f'{kind}.{lang}.html')
    if not os.path.exists(p):
        print(f'MISSING {kind}.{lang}.html'); return 1
    tr = open(p, encoding='utf-8').read()
    bad = 0
    # structure
    diffs = []
    for t in BLOCK:
        a = len(re.findall(rf'<{t}\b', ko, re.I)); b = len(re.findall(rf'<{t}\b', tr, re.I))
        if a != b:
            diffs.append(f'<{t}> {a} -> {b}')
    ha, hb = sorted(re.findall(r'href="([^"#][^"]*)"', ko)), sorted(re.findall(r'href="([^"#][^"]*)"', tr))
    if ha != hb:
        diffs.append(f'links differ: only in original {sorted(set(ha) - set(hb))[:6]}, only in translation {sorted(set(hb) - set(ha))[:6]}')
    print('STRUCTURE', 'ok' if not diffs else 'FAIL'); [print('  ', x) for x in diffs]; bad |= bool(diffs)
    # hangul
    left = [m for m in re.finditer(r'[^<>]{0,30}[가-힣][^<>]{0,30}', visible(tr))]
    left += [type('m', (), {'group': lambda s, x=a: x})() for a in attrs(tr) if HANGUL.search(a)]
    if kind == 'app':
        for m in re.finditer(r'["\'`][^"\'`\n]{0,60}[가-힣][^"\'`\n]{0,60}["\'`]', scripts(tr)):
            left.append(m)
    print('HANGUL', 'ok' if not left else f'FAIL ({len(left)})')
    for m in left[:25]:
        print('   ', m.group(0).strip()[:110])
    bad |= bool(left)
    # numbers
    na, nb = nums(visible(ko) + ' ' + ' '.join(attrs(ko))), nums(visible(tr) + ' ' + ' '.join(attrs(tr)))
    miss, extra = na - nb, nb - na
    print('NUMBERS', 'ok' if not miss and not extra else f'review: {sum(miss.values())} missing, {sum(extra.values())} new')
    if miss:
        print('   missing:', ', '.join(f'{k}×{v}' if v > 1 else k for k, v in sorted(miss.items()))[:900])
    if extra:
        print('   new:    ', ', '.join(f'{k}×{v}' if v > 1 else k for k, v in sorted(extra.items()))[:900])
    # images
    ib = []
    for s in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', tr):
        if s.startswith(('http', 'data:', '/')):
            continue
        if not os.path.exists(os.path.join(d, s)):
            ib.append(f'missing file {s}')
        else:
            base, ext = os.path.splitext(s)
            if not re.search(r'\.(en|es|ja)$|card-en-', base) and os.path.exists(os.path.join(d, f'{base}.{lang}.webp')):
                ib.append(f'{s} has a {lang} version: {base}.{lang}.webp')
    print('IMAGES', 'ok' if not ib else 'FAIL'); [print('  ', x) for x in ib]; bad |= bool(ib)
    m = FORBIDDEN.search(visible(tr))
    print('RULE', 'ok' if not m else f'FAIL "{m.group(0)}"'); bad |= bool(m)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
