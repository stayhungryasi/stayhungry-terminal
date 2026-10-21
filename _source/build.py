import sys, os, re, shutil, json, datetime
src, out, base = sys.argv[1], sys.argv[2], sys.argv[3].rstrip('/') + '/'
body = open(src, encoding='utf-8').read()
body = re.sub(r'^<title>.*?</title>\s*', '', body, count=1)
body = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', '', body, count=1)
meta = {
 'en': ('Stayhungry.ASI Terminal — market research hub', 'Megacap earnings countdowns, crisis signals and research like SpaceX 3Q26 decoded. One personal AI research hub. Press Esc when your boss walks by.'),
 'ko': ('Stayhungry.ASI Terminal — 시장 리서치 허브', '시총 순위, 실적 카운트다운, 위기 신호를 타입스크립트로 적어 일하는 화면처럼 보입니다. 누가 지나가면 Esc.'),
 'es': ('Stayhungry.ASI Terminal — hub de investigación de mercado', 'Rankings de megacaps, cuenta regresiva de resultados y señales de crisis escritos en TypeScript para que parezca trabajo. Pulsa Esc si se acerca tu jefe.'),
 'ja': ('Stayhungry.ASI Terminal — マーケットリサーチハブ', '時価総額ランキング、決算カウントダウン、危機シグナルをTypeScriptで記述。仕事中に見えます。上司が来たら Esc。'),
}
htmllang = {'en':'en','ko':'ko','es':'es-MX','ja':'ja'}
favicon = "data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230D111D'/%3E%3Cpath d='M8 11l6 5-6 5' stroke='%23E9B7A2' stroke-width='2.6' fill='none' stroke-linecap='round'/%3E%3Cpath d='M16 22h8' stroke='%23E9B7A2' stroke-width='2.6' stroke-linecap='round'/%3E%3C/svg%3E"
today = datetime.date.today().isoformat()
if os.path.exists(out): shutil.rmtree(out)
os.makedirs(out)
alts = ''.join(f'<link rel="alternate" hreflang="{htmllang[c]}" href="{base}{c}/">\n' for c in meta) + f'<link rel="alternate" hreflang="x-default" href="{base}en/">\n'
for c,(title,desc) in meta.items():
    os.makedirs(f'{out}/{c}')
    head = f'''<!doctype html>
<html lang="{htmllang[c]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{base}{c}/">
{alts}<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{base}{c}/">
<meta name="twitter:card" content="summary">
<meta name="twitter:site" content="@shaferwineX">
<meta name="theme-color" content="#0D111D">
<link rel="icon" href="{favicon}">
<script>window.SHA_LANG='{c}';window.SHA_PATHS=true;window.SHA_BUILD='{today}';</script>
</head>
<body>
'''
    open(f'{out}/{c}/index.html','w',encoding='utf-8').write(head + body + '\n</body>\n</html>\n')
redirect = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Stayhungry.ASI Terminal</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{alts}<link rel="canonical" href="{base}en/">
<script>(function(){{var L=['en','ko','es','ja'],p=null;try{{p=JSON.parse(localStorage.getItem('sha-lang'))}}catch(e){{}}
if(L.indexOf(p)<0){{var n=(navigator.language||'en').toLowerCase().slice(0,2);p=L.indexOf(n)>=0?n:'en'}}location.replace(p+'/');}})();</script>
<meta http-equiv="refresh" content="2;url=en/"></head><body style="background:#080A13;color:#A9AECB;font-family:monospace;padding:24px">
<a href="en/" style="color:#E9B7A2">Stayhungry.ASI Terminal →</a></body></html>
'''
open(f'{out}/index.html','w').write(redirect)
open(f'{out}/404.html','w').write(redirect.replace("location.replace(p+'/')", "location.replace('{0}'+p+'/')".format(base)).replace('url=en/','url='+base+'en/').replace('href="en/"','href="'+base+'en/"'))
sm = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for c in meta:
    sm.append(f'<url><loc>{base}{c}/</loc><lastmod>{today}</lastmod>' + ''.join(f'<xhtml:link rel="alternate" hreflang="{htmllang[x]}" href="{base}{x}/"/>' for x in meta) + '</url>')
sm.append('</urlset>')
open(f'{out}/sitemap.xml','w').write('\n'.join(sm)+'\n')
open(f'{out}/robots.txt','w').write(f'User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n')
open(f'{out}/.nojekyll','w').write('')
os.makedirs(f'{out}/data')
# open data API: run apiData() from the page's <script id="sha-data"> with node
import subprocess, tempfile
m = re.search(r'<script id="sha-data">(.*?)</script>', body, re.S)
if not m: sys.exit('sha-data script not found')
with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as tf:
    tf.write(m.group(1) + '\nprocess.stdout.write(JSON.stringify(apiData(process.argv[2])));\n')
api = json.loads(subprocess.check_output(['node', tf.name, today]).decode('utf-8'))
os.unlink(tf.name)
for name, obj in api.items():
    open(f'{out}/data/{name}', 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
open(f'{out}/data/README.md','w',encoding='utf-8').write(
"""# Stayhungry.ASI open data

Every number on the site, as JSON. Free to use; credit @stayhungryasi · https://t.me/stayhungryasi. Not investment advice.

Base URL: https://stayhungryasi.github.io/stayhungry-terminal/data/

| file | what |
|---|---|
| index.json | list of endpoints |
| earnings.json | megacap earnings dates (UTC), confirmed or estimated |
| crisis.json | crisis radar checks (SAMPLE until breaking_bot writes it) |
| megacaps.json | top 8 by market cap (SAMPLE) |
| spacex-3q26.json | SpaceX 3Q26 revenue mix and results vs consensus |
| changelog.json | site changelog |

```sh
curl -s https://stayhungryasi.github.io/stayhungry-terminal/data/earnings.json
```

Generated by `_source/build.py` from the page's `<script id="sha-data">`.
""")
print('built', sorted(os.listdir(out)))
