#!/usr/bin/env python3
"""English / Spanish / Japanese editions of the dashboard, made from the built Korean page.

  python3 translate6.py ../../../p/ai-models/index.html            # writes en/ es/ ja/ next to it, and adds the language bar to the Korean page
  python3 translate6.py ../../../p/ai-models/index.html --missing  # only list Korean text that has no translation yet (exit 1 if any)

How it works: seg6.py finds every piece of Korean text in the page (HTML text, attributes, JS strings; code-heavy JS templates
are cut into small pieces), tr6.json maps each piece to {en, es, ja}. Numbers, model names and code are never touched.
A piece with no translation stops the build and is listed: add it to tr6.json (same numbers, same ${...} expressions) and run again.
Monthly update: run build6.py first, then this; only the sentences that changed need new entries. stayhungryasi.com
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from seg6 import units, HG  # noqa: E402

LANGS = ['en', 'es', 'ja']
HTML_LANG = {'ko': 'ko', 'en': 'en', 'es': 'es', 'ja': 'ja'}
NAME = {'ko': '한국어', 'en': 'English', 'es': 'Español', 'ja': '日本語'}
URL = 'https://stayhungryasi.com/p/ai-models/'
WHOLE = ('기준 설정인 ', '1위는 ', ': 가장 낮은 단계에서')       # sentence templates translated as a whole (word order)
PIECE = re.compile(r'(?:[^<>`"{}$]|\$(?!\{))*[가-힣](?:[^<>`"{}$]|\$(?!\{))*')
MARK = '<!--langbar-->'


def pieces(s):
    """[(start, end, key)]: every span to replace, key = stripped Korean text."""
    out = []
    for a, b, k, t in units(s):
        if k == 'j`' and not any(h in t for h in WHOLE):
            for m in PIECE.finditer(t):
                out.append((a + m.start(), a + m.end()))
        else:
            out.append((a, b))
    res = []
    for a, b in out:
        t = s[a:b]
        l, r = len(t) - len(t.lstrip()), len(t) - len(t.rstrip())
        res.append((a + l, b - r, t.strip()))
    return res


def strip_bar(s):
    return re.sub(re.escape(MARK) + r'.*?' + re.escape(MARK), '', s, flags=re.S)


def bar(cur):
    links = ''.join(f'<a href="{URL}{"" if c == "ko" else c + "/"}{"?ko" if c == "ko" else ""}" data-lg="{c}" hreflang="{HTML_LANG[c]}"{" class=on" if c == cur else ""}>{NAME[c]}</a>' for c in ['en', 'ko', 'es', 'ja'])
    css = ('<style>.lgbar{display:flex;gap:6px;justify-content:flex-end;margin:0 0 10px;flex-wrap:wrap}.lgbar a{font-size:12.5px;line-height:1;padding:7px 11px;border-radius:999px;'
           'border:1px solid var(--line,#2a2f3a);color:var(--ink-2,#c3c9d6);text-decoration:none}.lgbar a.on{background:var(--ink,#fff);color:var(--bg,#0A0B0F);border-color:var(--ink,#fff);font-weight:600}'
           + ('body,button,input,select,textarea{font-family:"IBM Plex Sans KR","Noto Sans JP",system-ui,sans-serif}' if cur == 'ja' else '') + '</style>')
    js = ('<script>document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest(".lgbar a");if(a){try{localStorage.setItem("sha-lang",JSON.stringify(a.getAttribute("data-lg")))}catch(x){}}});</script>')
    return f'{MARK}{css}<nav class="lgbar" aria-label="Language">{links}</nav>{js}{MARK}'


def head_bits(cur):
    alt = ''.join(f'<link rel="alternate" hreflang="{HTML_LANG[c]}" href="{URL}{"" if c == "ko" else c + "/"}">' for c in ['ko'] + LANGS)
    alt += f'<link rel="alternate" hreflang="x-default" href="{URL}en/">'
    redir = ''
    if cur == 'ko':   # same rule as the research pages: a reader whose language is en/es/ja goes to that edition, ?ko pins Korean
        redir = ('<script>(function(){var L=["en","es","ja"],p=null;try{p=JSON.parse(localStorage.getItem("sha-lang"))}catch(e){}'
                 'if(["en","ko","es","ja"].indexOf(p)<0){var n=(navigator.language||"en").toLowerCase().slice(0,2);p=["ko","es","ja"].indexOf(n)>=0?n:"en"}'
                 'if(L.indexOf(p)>=0&&!/[?&]ko\\b/.test(location.search)&&!/bot|crawl|spider|slurp|preview/i.test(navigator.userAgent))location.replace("' + URL.replace('https://stayhungryasi.com', '') + '"+p+"/"+location.hash)})();</script>')
    font = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap">' if cur == 'ja' else ''
    return f'{MARK}{alt}{redir}{font}{MARK}'


def dress(s, cur):
    s = strip_bar(s)
    s = s.replace('</head>', head_bits(cur) + '</head>', 1)
    s = s.replace('<header class="brandbar">', bar(cur) + '<header class="brandbar">', 1)
    return s


def main():
    src = sys.argv[1]
    only_missing = '--missing' in sys.argv
    ko = strip_bar(open(src, encoding='utf-8').read())
    TR = json.load(open(os.path.join(HERE, 'tr6.json'), encoding='utf-8'))
    P = pieces(ko)
    miss = sorted({k for a, b, k in P if k not in TR or any(not TR[k].get(c) for c in LANGS)})
    if miss:
        print(f'{len(miss)} Korean text piece(s) have no translation in tr6.json:')
        for k in miss:
            print('  ', json.dumps(k, ensure_ascii=False))
        sys.exit(1)
    if only_missing:
        print('all', len({k for a, b, k in P}), 'pieces translated'); return
    for c in LANGS:
        out, pos = [], 0
        for a, b, k in P:
            out.append(ko[pos:a]); out.append(TR[k][c]); pos = b
        out.append(ko[pos:])
        t = ''.join(out)
        t = t.replace('<html lang="ko">', f'<html lang="{HTML_LANG[c]}">', 1)
        t = t.replace(f'<link rel="canonical" href="{URL}">', f'<link rel="canonical" href="{URL}{c}/">').replace(f'<meta property="og:url" content="{URL}">', f'<meta property="og:url" content="{URL}{c}/">')
        t = dress(t, c)
        left = [m.group(0) for m in re.finditer(r'[^\n]{0,30}[가-힣]+[^\n]{0,30}', strip_bar(t))]
        if left:
            print(c, 'Korean left:', left[:5]); sys.exit(1)
        d = os.path.join(os.path.dirname(os.path.abspath(src)), c)
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(t)
        print('wrote', os.path.relpath(os.path.join(d, 'index.html')))
    open(src, 'w', encoding='utf-8').write(dress(ko, 'ko'))
    print('language bar added to', os.path.relpath(src))


if __name__ == '__main__':
    main()
