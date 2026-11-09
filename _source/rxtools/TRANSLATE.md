# Translating stayhungryasi.com research (Korean original → EN / ES / JA)

The site publishes each report in `_source/research/<slug>/`. The Korean original stays the source of truth.
Translations are faithful versions of it for English, Spanish and Japanese readers. Nothing is added, nothing is dropped.

## Files you write (and nothing else)

| report kind | original | write |
|---|---|---|
| document | `body.html` | `body.en.html`, `body.es.html`, `body.ja.html` |
| interactive | `app.html` (+ `datasets.json`) | `app.en.html` … (+ `datasets.<lang>.json` if the data file has Korean labels; point the fetch in `app.<lang>.html` at it) |
| images | `card-07.webp`, `chart-2.webp` … | `card-07.<lang>.webp` via `img_render.py` (see Images) |

Do not edit `body.html`, `app.html`, `meta.json`, other reports, `page.html` or anything outside your report folder
(image specs go in `_source/rxtools/specs/<slug>/`). Do not run git. Do not publish.

## Translation rules

1. **Faithful.** Same claims, same hedges, same order, same emphasis. No new facts, no softening, no added opinion.
   Never add buy/sell/allocation language. "작성자 판단", estimates and probabilities stay marked as such.
2. **Numbers do not change.** Copy every figure exactly (digits, signs, decimals, %, $, dates). Keep a decimal point
   (no decimal commas, also in Spanish). Korean units:
   - EN: 조 = trillion, 억 = 100 million (4,500억원 → KRW 450 billion).
   - ES (long scale): 1조 = un billón (10^12), 억 = cien millones (4,500억원 → 450 mil millones de wones). Never write
     "trillón" for 조.
     Converting can change the digits (4500 → 450). That is allowed; it must be the same value. List every such
     conversion in your report.
   - JA: keep 兆 / 億 / 万 (same system), so digits stay identical. 원 → ウォン.
   - Currencies: ₩ / KRW for won, keep $ as is.
3. **Dates.** Keep ISO dates as written (2026-11-06). Korean "11월 6일" → "Nov 6" / "6 de noviembre" / "11月6日".
4. **Names.** Companies, tickers, people, indices: standard names in that language (SK하이닉스 → SK hynix,
   코스피 → KOSPI, 금융투자협회 → Korea Financial Investment Association (KOFIA), 엔비디아 → Nvidia).
   Korean-only market slang (빚투, 동학개미…) → translate the meaning, keep it short.
5. **Register.**
   - EN: clear US English research prose, short sentences, no hype.
   - ES: neutral Latin American Spanish (es-MX), impersonal research tone.
   - JA: research tone, だ・である調, half-width digits, full-width Japanese punctuation.
6. **Link text** is translated unless it is a publication or document title; the `href` never changes.
7. The site credit stays `stayhungryasi.com`.

## HTML rules

- Keep the exact tag structure, classes, ids, inline styles, `href`s and the order of elements. Translate text nodes and the
  attributes people see: `alt`, `title`, `aria-label`, `placeholder`, table cells, `figcaption`, SVG `<text>`/`<tspan>`.
- Inline SVG charts: translate the `<text>` contents. If a label gets longer, shorten it sensibly or lower its `font-size`
  a little; do not move coordinates unless it would overlap.
- Images: point `src` at the localized file for your language (see the table in your task). Keep `width`/`height`.
- Interactive apps: translate every Korean string in HTML and in JS string literals (labels, tooltips, legends, number
  formatters like "조원"), keep the logic. Load the page once in Playwright and make sure there are no JS errors:
  ```
  cd _source/research/<slug> && python3 -m http.server <port 9100-9199> &
  node -e "const {chromium}=require('/home/claude/.npm-global/lib/node_modules/playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();const e=[];p.on('pageerror',x=>e.push(x.message));await p.goto('http://localhost:<port>/app.en.html');await p.waitForTimeout(2500);console.log('errors',e);await b.close();})()"
  ```

## Long files

Translate in pieces so nothing is cut off: split the original at `<h2` (or every ~12 KB) with a short Python script into
`/tmp/rx/<slug>/<lang>/part-NN.html`, translate each piece into `…/part-NN.<lang>.html`, then join them in order into the
final file. Check the joined file starts and ends like the original.

## Check (required)

```
python3 _source/rxtools/check_tr.py <slug> <lang>
```
- STRUCTURE, HANGUL, RULE must say ok. IMAGES must say ok, except files another worker is still creating
  (names listed in your task) — note that in your report.
- NUMBERS is a review list: go through every missing/new number and fix real mistakes. In your final report explain each
  remaining one in one line (e.g. "4500 → 450: 4,500억원 = KRW 450 billion").

## Images (only for image tasks)

For each image: detect, look, write a spec, render, look again, fix until clean.
```
python3 _source/rxtools/img_detect.py _source/research/<slug>/<img> _source/rxtools/specs/<slug>
#  → specs/<slug>/<name>.boxes.json, <name>.boxes.png (+ -top/-bottom enlarged halves). Look at them with Read.
#  write specs/<slug>/<name>.json (format in the img_render.py docstring; example: specs/railroad-vs-semis-130y/card-04.json)
python3 _source/rxtools/img_render.py _source/rxtools/specs/<slug>/<name>.json        # writes <name>.<lang>.webp
```
- Look at every rendered image (Read the .webp). Acceptance: no Korean left anywhere, nothing clipped or overlapping,
  sizes and weights match the original's hierarchy, colours/highlights kept, every number identical, graphics intact.
- Tips: group the OCR fragments of one sentence into one region; set `size` when the estimate looks too big or small;
  `expand` (negative values move an edge inward, e.g. to start after a legend swatch); `keep` to restore swatches/bars that an
  erase touched; `erase` for stray Korean the detector missed; `==accent==` and `**heavier**` for coloured/bold words.
- Text that is only numbers, tickers or English already: leave it (do not list it in a region).
- Use one consistent wording per term across all images of the report (and with the body translation where you can see it).
