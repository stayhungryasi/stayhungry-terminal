# Stayhungry.ASI Terminal

A market observatory disguised as a code editor. Live at **https://stayhungryasi.com/**

- Languages: `/en/` (default) · `/ko/` · `/es/` · `/ja/`
- `_source/page.html` is the single source page. Rebuild all language pages into a scratch
  directory (build.py wipes its output directory first, so never point it at the repo), then copy:
  ```sh
  python3 _source/build.py _source/page.html /tmp/sha-build https://stayhungryasi.com
  cp -r /tmp/sha-build/en /tmp/sha-build/ko /tmp/sha-build/es /tmp/sha-build/ja /tmp/sha-build/data .
  cp /tmp/sha-build/index.html /tmp/sha-build/404.html /tmp/sha-build/sitemap.xml /tmp/sha-build/robots.txt .
  ```
- `data/` receives JSON feeds from the bots.

Not investment advice. Telegram: @stayhungryasi · https://t.me/stayhungryasi
