#!/usr/bin/env python3
"""
Research library builder for stayhungryasi.com

  python _source/research.py <outdir> [base_url]

Reads every _source/research/<slug>/ folder:
  meta.json   title / dek / key number / 3 points / tags / checkpoints in 4 languages (en, ko, es, ja)
  body.html   the report itself (Korean original), already cleaned            -- kind "doc"
  app.html    an interactive report (dashboard, charts) served as-is in a frame -- kind "page"
  datasets.json, other files are copied next to the page

Writes into <outdir>:
  r/<slug>/index.html   one page per report (4-language brief + full Korean original)
  r/index.html          static library index (for search engines and no-JS readers)
  r/feed.xml            RSS feed, newest first
  data/research.json    open data: every report's metadata + upcoming checkpoints
and prints the report URLs (build.py adds them to sitemap.xml).

Publishing rule: pure research only. No employer, real name, PB/client or internal-review content,
no direct buy/sell/allocation instructions. check() refuses to build if any of that slips in.
@stayhungryasi · https://t.me/stayhungryasi
"""
import html, json, os, re, shutil, sys, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'research')
LANGS = ['en', 'ko', 'es', 'ja']
HTML_LANG = {'en': 'en', 'ko': 'ko', 'es': 'es-MX', 'ja': 'ja'}
CAT = {
    'macro': {'en': 'Macro', 'ko': '거시', 'es': 'Macro', 'ja': 'マクロ'},
    'ai': {'en': 'AI infrastructure', 'ko': 'AI 인프라', 'es': 'Infraestructura IA', 'ja': 'AIインフラ'},
    'sector': {'en': 'Sectors', 'ko': '섹터', 'es': 'Sectores', 'ja': 'セクター'},
    'crypto': {'en': 'Crypto', 'ko': '크립토', 'es': 'Cripto', 'ja': 'クリプト'},
    'masters': {'en': 'Investors', 'ko': '투자 거장', 'es': 'Inversionistas', 'ja': '投資家'},
}
UI = {
    'en': dict(back='← Research library', orig='ORIGINAL IN KOREAN', brief='BRIEF', key='KEY NUMBER', checks='CHECKPOINTS', related='MORE RESEARCH', read='Read the full report ↓', minutes='{n} min read', sources='{n} sources', asof='Data as of {d}', date='Published {d}', open='Open the interactive report in a new tab ↗', note='AI-assisted research by @stayhungryasi. Written on the date shown; numbers may have changed since. Not investment advice.'),
    'ko': dict(back='← 리서치 라이브러리', orig='원문 한국어', brief='요약', key='핵심 숫자', checks='검증 일정', related='다른 리서치', read='원문 전체 읽기 ↓', minutes='{n}분 분량', sources='출처 {n}개', asof='데이터 기준 {d}', date='작성 {d}', open='인터랙티브 리포트 새 창으로 열기 ↗', note='AI 도움을 받아 @stayhungryasi가 작성한 리서치입니다. 작성일 기준이며 이후 숫자가 바뀌었을 수 있습니다. 투자 권유가 아닙니다.'),
    'es': dict(back='← Biblioteca de investigación', orig='ORIGINAL EN COREANO', brief='RESUMEN', key='CIFRA CLAVE', checks='PUNTOS DE CONTROL', related='MÁS INVESTIGACIÓN', read='Leer el informe completo ↓', minutes='{n} min de lectura', sources='{n} fuentes', asof='Datos al {d}', date='Publicado {d}', open='Abrir el informe interactivo en otra pestaña ↗', note='Investigación asistida por IA de @stayhungryasi. Vigente a la fecha indicada; las cifras pueden haber cambiado. No es asesoría de inversión.'),
    'ja': dict(back='← リサーチライブラリ', orig='原文は韓国語', brief='要約', key='重要な数字', checks='検証スケジュール', related='ほかのリサーチ', read='全文を読む ↓', minutes='{n}分で読める', sources='出典{n}件', asof='データ基準 {d}', date='作成 {d}', open='インタラクティブ版を新しいタブで開く ↗', note='AIの支援を受けて@stayhungryasiが作成したリサーチです。作成日時点の内容で、その後数値が変わっている可能性があります。投資助言ではありません。'),
}
FORBIDDEN = re.compile(r'하나증권|Centerfield|김광모|광모|대표님|필승|PB 활용|고객 설명|고객용|고객 성향|내부 투자검토|투자위원회|등록 투자자문|Investment Committee|예시 비중|분할 매수|매수할 기회|분할로 사면')
FAV = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230D111D'/%3E"
       "%3Cpath d='M8 11l6 5-6 5' stroke='%23E9B7A2' stroke-width='2.6' fill='none' stroke-linecap='round'/%3E%3Cpath d='M16 22h8' stroke='%23E9B7A2' stroke-width='2.6' stroke-linecap='round'/%3E%3C/svg%3E")
E = html.escape


def text_of(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>', ' ', h, flags=re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()


def check(slug, *texts):
    for t in texts:
        m = FORBIDDEN.search(t)
        if m:
            sys.exit(f'research/{slug}: refusing to publish, found "{m.group(0)}" (pure research only)')


def load():
    out = []
    for slug in sorted(os.listdir(SRC)):
        d = os.path.join(SRC, slug)
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, 'meta.json')):
            continue
        m = json.load(open(os.path.join(d, 'meta.json'), encoding='utf-8'))
        m['slug'] = slug
        m['kind'] = 'page' if os.path.exists(os.path.join(d, 'app.html')) else 'doc'
        body = open(os.path.join(d, 'body.html' if m['kind'] == 'doc' else 'app.html'), encoding='utf-8').read()
        if m['kind'] == 'page' and os.path.exists(os.path.join(d, 'datasets.json')):
            body_text = text_of(body) + ' ' + open(os.path.join(d, 'datasets.json'), encoding='utf-8').read()
        else:
            body_text = text_of(body)
        check(slug, body_text, json.dumps(m, ensure_ascii=False))
        m['_body'] = body
        m['_dir'] = d
        chars = len(re.sub(r'\s', '', body_text))
        m['minutes'] = max(2, round(chars / 600))          # ~600 Korean characters a minute
        extra = open(os.path.join(d, 'datasets.json'), encoding='utf-8').read() if os.path.exists(os.path.join(d, 'datasets.json')) else ''
        m['sources'] = len(set(re.findall(r'href="(https?://[^"]+)"', body)) | set(re.findall(r'"(https?://[^"\s]+)"', extra)))
        out.append(m)
    out.sort(key=lambda m: (m['date'], m['slug']), reverse=True)
    return out


CSS = '''
:root{--bg:#0A0C10;--card:#12161E;--line:#1D2330;--line2:#2E3445;--ink:#EEF0F5;--ink2:#C3C9D6;--mute:#8D95A8;--or:#F26522;--mono:"IBM Plex Mono",ui-monospace,monospace}
*{box-sizing:border-box}[hidden]{display:none!important}html{scroll-padding-top:64px}
body{margin:0;background:var(--bg);color:var(--ink2);font:16px/1.75 "Noto Sans KR",system-ui,sans-serif}
a{color:var(--or)}
.top{position:sticky;top:0;z-index:5;background:#0A0C10ee;backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.top .in{max-width:980px;margin:0 auto;padding:12px 20px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.brand{font-family:var(--mono);font-size:13px;letter-spacing:.2em;color:var(--ink);text-decoration:none;font-weight:600;white-space:nowrap}
.brand i{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--or);margin-right:10px;vertical-align:1px}
.top a.back{font-family:var(--mono);font-size:12.5px;color:var(--or);text-decoration:none;white-space:nowrap;min-width:0;overflow:hidden;text-overflow:ellipsis}
main{max-width:980px;margin:0 auto;padding:30px 20px 60px}
.eb{font-family:var(--mono);font-size:12.5px;letter-spacing:.18em;color:var(--or);text-transform:uppercase}
h1.t{color:var(--ink);font-size:clamp(28px,4.6vw,46px);line-height:1.2;font-weight:900;margin:.3em 0 .35em;letter-spacing:-.01em}
.meta{font-family:var(--mono);font-size:12.5px;color:var(--mute);display:flex;flex-wrap:wrap;gap:6px 16px}
.brief{margin:26px 0 30px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 24px}
.lt{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:14px}
.lt button{font:600 12.5px var(--mono);letter-spacing:.06em;color:var(--ink2);background:none;border:1px solid var(--line2);border-radius:999px;padding:6px 12px;cursor:pointer}
.lt button.on{background:var(--or);border-color:var(--or);color:#0A0C10}
.bp[hidden]{display:none}
.dek{color:var(--ink);font-size:clamp(19px,2.3vw,24px);font-weight:800;line-height:1.45;margin:0 0 16px}
.kg{display:grid;grid-template-columns:minmax(0,220px) minmax(0,1fr);gap:20px;align-items:start}
.kv b{display:block;font-size:clamp(34px,5vw,52px);font-weight:900;color:var(--or);line-height:1.05;letter-spacing:-.02em;word-break:keep-all}
.kv small,.lbl{display:block;font-family:var(--mono);font-size:11.5px;letter-spacing:.14em;color:var(--mute);margin:6px 0}
.pts{margin:0;padding-left:20px}.pts li{margin:4px 0}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:14px}.chips span{font-family:var(--mono);font-size:12px;border:1px solid var(--line2);border-radius:999px;padding:3px 10px;color:var(--ink2)}
.ck{margin:12px 0 0;padding:0;list-style:none}.ck li{font-size:14.5px;margin:3px 0}.ck time{font-family:var(--mono);color:var(--or);margin-right:8px}
.note{font-size:13px;color:var(--mute);border:1px dashed var(--line2);border-radius:10px;padding:10px 14px;margin:18px 0 0;line-height:1.6}
.doc h2{color:var(--ink);font-size:clamp(21px,2.6vw,27px);font-weight:900;margin:2em 0 .5em;padding-top:.6em;border-top:1px solid var(--line);line-height:1.35}
.doc h3{color:var(--ink);font-size:19px;font-weight:800;margin:1.5em 0 .4em}
.doc b{color:var(--ink)}.doc li p{margin:.2em 0}
.doc ul.check{list-style:none;padding-left:4px}.doc ul.check li:before{content:"☐ ";color:var(--or)}
.doc blockquote{margin:16px 0;border-left:3px solid var(--or);padding:4px 16px;color:var(--ink2)}
.doc hr{border:0;border-top:1px solid var(--line);margin:24px 0}
.tw{overflow-x:auto;margin:14px 0;border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.55}
th,td{text-align:left;vertical-align:top;padding:8px 11px;border-bottom:1px solid var(--line)}
th{background:var(--card);color:var(--ink);font-weight:700}th p,td p{margin:0}
figure.fig{margin:20px 0;background:#fcfcfb;border-radius:12px;padding:12px;overflow-x:auto}
figure.fig svg{width:100%;height:auto;min-width:560px;display:block;
 --cds-text-primary:#141413;--cds-text-secondary:#5E5D59;--cds-chart-axis:#9A988F;--cds-chart-muted:#C9C7BD;--cds-chart-reference:#7B7A73;--cds-chart-categorical-1:#D9480F;--cds-chart-reference-tint:#F0EEE6}
figure.fig figcaption{font-size:12.5px;color:#5E5D59;margin-top:6px}
.frame{width:100%;border:1px solid var(--line);border-radius:14px;background:#0A0C10;min-height:80vh;display:block}
.wide{max-width:1240px}body.w .top .in,body.w footer{max-width:1240px}
.rel{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-top:12px}
.rel a{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;text-decoration:none;color:var(--ink2)}
.rel a:hover{border-color:var(--or)}.rel b{display:block;color:var(--ink);font-size:16px;line-height:1.4}.rel small{font-family:var(--mono);font-size:11.5px;color:var(--mute)}
footer{max-width:980px;margin:0 auto;padding:20px;border-top:1px solid var(--line);font-family:var(--mono);font-size:12.5px;color:var(--mute);display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
footer a{color:var(--mute);text-decoration:none}
@media (max-width:640px){.kg{grid-template-columns:1fr}.brief{padding:16px}main{padding:22px 16px 48px}}
'''

LANG_JS = '''<script>
(function(){var L=['en','ko','es','ja'],p=null;try{p=JSON.parse(localStorage.getItem('sha-lang'))}catch(e){}
if(L.indexOf(p)<0){var n=(navigator.language||'en').toLowerCase().slice(0,2);p=L.indexOf(n)>=0?n:'en'}
function set(c){document.querySelectorAll('[data-l]').forEach(function(e){e.hidden=e.getAttribute('data-l')!==c});
document.querySelectorAll('.lt button').forEach(function(b){b.classList.toggle('on',b.getAttribute('data-set')===c)});
document.querySelectorAll('a[data-lib]').forEach(function(a){a.href='/'+c+'/#library'});}
document.addEventListener('click',function(e){var b=e.target.closest('[data-set]');if(b){set(b.getAttribute('data-set'));try{localStorage.setItem('sha-lang',JSON.stringify(b.getAttribute('data-set')))}catch(x){}}});
set(p);})();
</script>'''

FRAME_JS = '''<script>
(function(){var f=document.getElementById('app');function fit(){try{var d=f.contentDocument;if(d&&d.body){f.style.height=Math.max(600,d.documentElement.scrollHeight)+'px'}}catch(e){}}
f.addEventListener('load',function(){fit();try{new ResizeObserver(fit).observe(f.contentDocument.body)}catch(e){setInterval(fit,1000)}});})();
</script>'''


def head(title, desc, url, lang='ko', extra=''):
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary"><meta name="twitter:site" content="@shaferwineX">
<meta name="theme-color" content="#0A0C10"><link rel="icon" href="{FAV}">
<link rel="alternate" type="application/rss+xml" title="Stayhungry.ASI research" href="/r/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+KR:wght@400;700;900&display=swap" rel="stylesheet">
<style>{CSS}</style>{extra}
</head>
<body>
'''


def topbar():
    return ('<header class="top"><div class="in"><a class="brand" href="/"><i></i>STAY HUNGRY.ASI</a>'
            + ''.join(f'<a class="back" data-l="{c}" data-lib href="/{c}/#library"{"" if c == "en" else " hidden"}>{E(UI[c]["back"])}</a>' for c in LANGS)
            + '</div></header>')


FOOT = ('<footer><span>Not investment advice. 투자 권유 아님.</span>'
        '<a href="https://t.me/stayhungryasi" target="_blank" rel="noopener">@stayhungryasi · https://t.me/stayhungryasi</a></footer>')


def brief(m):
    tabs = '<div class="lt" role="tablist">' + ''.join(
        f'<button data-set="{c}" class="{"on" if c == "en" else ""}">{ {"en": "EN", "ko": "한국어", "es": "ES", "ja": "日本語"}[c] }</button>' for c in LANGS) + '</div>'
    panes = []
    for c in LANGS:
        u = UI[c]
        ck = ''
        if m.get('checkpoints'):
            ck = f'<p class="lbl">{E(u["checks"])}</p><ul class="ck">' + ''.join(
                f'<li><time datetime="{E(x["date"])}">{E(x["date"])}</time>{E(x["text"][c])}</li>' for x in m['checkpoints']) + '</ul>'
        tags = m.get('tags', {}).get(c, [])
        chips = ''.join(f'<span>{E(t)}</span>' for t in dict.fromkeys(m.get('tickers', [])[:10] + tags))
        panes.append(f'''<div class="bp" data-l="{c}"{"" if c == "en" else " hidden"}>
<p class="dek">{E(m["dek"][c])}</p>
<div class="kg"><div class="kv"><small>{E(u["key"])}</small><b>{E(m["key"]["value"])}</b><small style="letter-spacing:.04em;text-transform:none">{E(m["key"]["label"][c])}</small></div>
<div><p class="lbl">{E(u["brief"])}</p><ul class="pts">{"".join(f"<li>{E(p)}</li>" for p in m["points"][c])}</ul>{ck}</div></div>
<div class="chips">{chips}</div>
<p class="note">{E(u["note"])}</p></div>''')
    return '<section class="brief">' + tabs + ''.join(panes) + '</section>'


def meta_line(m):
    out = []
    for c in LANGS:
        u = UI[c]
        bits = [CAT[m['category']][c], u['date'].format(d=m['date']), u['asof'].format(d=m['asof']), u['minutes'].format(n=m['minutes'])]
        if m['sources']:
            bits.append(u['sources'].format(n=m['sources']))
        out.append(f'<div class="meta" data-l="{c}"{"" if c == "en" else " hidden"}>' + ''.join(f'<span>{E(b)}</span>' for b in bits) + '</div>')
    return ''.join(out)


def related(m, allm):
    others = [x for x in allm if x['slug'] != m['slug']]
    same = [x for x in others if x['category'] == m['category']]
    pick = (same + [x for x in others if x not in same])[:3]
    blocks = []
    for c in LANGS:
        blocks.append(f'<div data-l="{c}"{"" if c == "en" else " hidden"}><p class="lbl" style="margin-top:40px">{E(UI[c]["related"])}</p><div class="rel">' + ''.join(
            f'<a href="/r/{x["slug"]}/"><small>{E(CAT[x["category"]][c])} · {E(x["date"])}</small><b>{E(x["title"][c])}</b></a>' for x in pick) + '</div></div>')
    return ''.join(blocks)


def page(m, allm, base):
    url = f'{base}r/{m["slug"]}/'
    title = f'{m["title"]["ko"]} · {m["title"]["en"]} · Stayhungry.ASI'
    desc = f'{m["dek"]["en"]} {m["dek"]["ko"]}'
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": m['title']['en'], "alternativeHeadline": m['title']['ko'],
          "inLanguage": "ko", "datePublished": m['date'], "description": m['dek']['en'], "url": url,
          "author": {"@type": "Organization", "name": "Stayhungry.ASI", "url": base},
          "publisher": {"@type": "Organization", "name": "Stayhungry.ASI", "url": base}}
    extra = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>'
    eb = ''.join(f'<p class="eb" data-l="{c}"{"" if c == "en" else " hidden"}>RESEARCH · {E(CAT[m["category"]][c])} · {E(UI[c]["orig"])}</p>' for c in LANGS)
    if m['kind'] == 'doc':
        body = f'<article class="doc" id="full" lang="ko">{m["_body"]}</article>'
        wide = ''
    else:
        body = (f'<p id="full"><a href="app.html" target="_blank" rel="noopener">{E(UI["ko"]["open"])}</a></p>'
                f'<iframe id="app" class="frame" src="app.html" title="{E(m["title"]["ko"])}" loading="lazy"></iframe>{FRAME_JS}')
        wide = ' class="wide"'
    return (head(title, desc, url, 'ko', extra).replace('<body>', '<body class="w">' if wide else '<body>') + topbar() + f'<main{wide}>' + eb
            + f'<h1 class="t" lang="ko">{E(m["title"]["ko"])}</h1>'
            + ''.join(f'<p class="meta" data-l="{c}" style="font-size:15px;color:var(--ink2);font-family:inherit"{"" if c == "en" else " hidden"} lang="{HTML_LANG[c]}">{E(m["title"][c])}</p>' for c in LANGS if c != 'ko')
            + meta_line(m) + brief(m) + body + related(m, allm) + '</main>' + FOOT + LANG_JS + '</body></html>\n')


def index_page(allm, base):
    url = f'{base}r/'
    rows = ''.join(f'''<a href="/r/{m["slug"]}/"><small>{E(CAT[m["category"]]["en"])} · {E(m["date"])}</small><b>{E(m["title"]["en"])}</b><span lang="ko">{E(m["title"]["ko"])}</span><p>{E(m["dek"]["en"])}</p></a>''' for m in allm)
    css = '<style>.rel a span{display:block;font-size:14px;color:var(--ink2);margin-top:2px}.rel a p{margin:8px 0 0;font-size:14px;color:var(--mute);line-height:1.55}</style>'
    return (head('Research library · Stayhungry.ASI', f'{len(allm)} research reports by @stayhungryasi: AI infrastructure, macro, sectors, crypto, great investors. Korean originals with briefs in 4 languages.', url, 'en', css)
            + topbar() + f'<main><p class="eb">RESEARCH LIBRARY · {len(allm)}</p><h1 class="t">Research, in full.</h1>'
            + '<p>Every report is hosted here in its Korean original, with a brief in English, Korean, Spanish and Japanese. Interactive version: <a href="/en/#library">open the library</a> · RSS: <a href="/r/feed.xml">/r/feed.xml</a> · JSON: <a href="/data/research.json">/data/research.json</a></p>'
            + f'<div class="rel">{rows}</div></main>' + FOOT + '</body></html>\n')


def rss(allm, base):
    def d(s):
        return datetime.datetime.strptime(s, '%Y-%m-%d').strftime('%a, %d %b %Y 00:00:00 +0900')
    items = ''.join(f'''<item><title>{E(m["title"]["en"])} · {E(m["title"]["ko"])}</title><link>{base}r/{m["slug"]}/</link><guid>{base}r/{m["slug"]}/</guid><pubDate>{d(m["date"])}</pubDate><description>{E(m["dek"]["en"] + " " + m["dek"]["ko"])}</description></item>''' for m in allm)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Stayhungry.ASI research</title><link>{base}r/</link><description>Research by @stayhungryasi · https://t.me/stayhungryasi. Not investment advice.</description>{items}</channel></rss>
'''


def build(out, base='https://stayhungryasi.com/'):
    allm = load()
    os.makedirs(os.path.join(out, 'r'), exist_ok=True)
    os.makedirs(os.path.join(out, 'data'), exist_ok=True)
    urls = []
    for m in allm:
        d = os.path.join(out, 'r', m['slug'])
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(m['_dir']):
            if f not in ('meta.json', 'body.html'):
                shutil.copy(os.path.join(m['_dir'], f), os.path.join(d, f))
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page(m, allm, base))
        urls.append(f'{base}r/{m["slug"]}/')
    open(os.path.join(out, 'r', 'index.html'), 'w', encoding='utf-8').write(index_page(allm, base))
    open(os.path.join(out, 'r', 'feed.xml'), 'w', encoding='utf-8').write(rss(allm, base))
    today = datetime.date.today().isoformat()
    pub = [{k: v for k, v in m.items() if not k.startswith('_')} | {'url': f'{base}r/{m["slug"]}/'} for m in allm]
    upcoming = sorted([dict(c, slug=m['slug']) for m in allm for c in m.get('checkpoints', []) if c['date'] >= today], key=lambda c: c['date'])
    doc = {'name': 'Stayhungry.ASI research library', 'updated': today, 'count': len(pub), 'feed': f'{base}r/feed.xml',
           'rule': 'Pure research only: no affiliation, client or internal-review content, no buy/sell instructions. Korean originals; briefs in 4 languages. Not investment advice.',
           'credit': '@stayhungryasi · https://t.me/stayhungryasi', 'categories': CAT, 'reports': pub, 'upcoming_checkpoints': upcoming}
    open(os.path.join(out, 'data', 'research.json'), 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
    urls.append(f'{base}r/')
    return urls


if __name__ == '__main__':
    out = sys.argv[1]
    base = (sys.argv[2].rstrip('/') + '/') if len(sys.argv) > 2 else 'https://stayhungryasi.com/'
    for u in build(out, base):
        print(u)
