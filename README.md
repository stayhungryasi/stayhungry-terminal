# Stayhungry.ASI Terminal

A market observatory disguised as a code editor. Live at **https://stayhungryasi.com/**

- Languages: `/en/` (default) · `/ko/` · `/es/` · `/ja/`
- `_source/page.html` is the single source page. Rebuild all language pages into a scratch
  directory (build.py wipes its output directory first, so never point it at the repo), then copy:
  ```sh
  python3 -B _source/build.py _source/page.html /tmp/sha-build https://stayhungryasi.com
  cp -r /tmp/sha-build/en /tmp/sha-build/ko /tmp/sha-build/es /tmp/sha-build/ja /tmp/sha-build/data .
  cp /tmp/sha-build/index.html /tmp/sha-build/404.html /tmp/sha-build/sitemap.xml /tmp/sha-build/robots.txt .
  rm -rf r && cp -r /tmp/sha-build/r r
  ```
- `data/` and `live/` also receive JSON feeds from the bots (crisis, fear). The build never writes those files.

## Research library (`/r/`)

Every research report lives in `_source/research/<slug>/`:

| file | what |
|---|---|
| `meta.json` | date, asof, category (macro · ai · sector · crypto · masters), title/dek/points in en·ko·es·ja, key number, tickers, tags, checkpoints |
| `body.html` | the Korean original as clean HTML (charts as inline SVG) |
| `app.html` (+ `datasets.json`) | instead of body.html: an interactive report served as-is in a frame |

`_source/research.py` (called by build.py) turns that into `r/<slug>/index.html`, `r/index.html`,
`r/feed.xml` and `data/research.json`, adds the pages to the sitemap, and inlines the list into the
reader page (RESEARCH tab) and the dev view (`research/LIBRARY.md`, `data/research.json`, chat command `research`).

Publishing rule: pure research only. No affiliation, real name, PB/client or internal-review material,
and no buy/sell or allocation instructions. research.py refuses to build if it finds any of that.
Every number in a brief must appear in the original.

Not investment advice. Telegram: @stayhungryasi · https://t.me/stayhungryasi
