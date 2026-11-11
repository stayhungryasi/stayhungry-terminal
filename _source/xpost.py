#!/usr/bin/env python3
"""Daily X post of the brief (English): one card image with the 3 lines + a one-line hook + the hub link.

  python3 _source/xpost.py --dry [--out card.png]   # build the text and the card, post nothing
  python3 _source/xpost.py                           # post (needs X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET)

Runs from .github/workflows/x-daily.yml at 21:37 KST (US pre-market). Rules:
  - only today's brief (data/brief.json date == today KST); a stale brief is never posted
  - once a day: live/x-post.json remembers the last post
  - global-first order: brief.json "x.order" if the editor gave one, else a score by page and Korea-only wording
  - the hook is the lead line (brief.json "x.hook" if given); link: stayhungryasi.com/en/#brief (LINK=0 drops it)
  - same publishing rule as the hub: FORBIDDEN wording stops the post
stayhungryasi.com
"""
import base64, datetime as dt, hashlib, hmac, json, os, re, secrets, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KST = dt.timezone(dt.timedelta(hours=9))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from research import FORBIDDEN  # noqa: E402

URL = "https://stayhungryasi.com/en/#brief"
PAGE_SCORE = {"spcxlock": 9, "agent": 9, "rank": 7, "radar": 7, "buffett": 7, "vix": 7, "fear": 7, "library": 6, "research": 6,
              "mix": 6, "score": 6, "earnings": 5, "univertrix": 5, "uvmap": 5, "schedule": 4, "leverage": 1, "filings": 1}
KOREA = re.compile(r"\b(KOSPI|KOSDAQ|Korea[n]?|Samsung|SK [A-Z]\w+|Hyundai|LG|Kakao|Naver|DART|KRW|won)\b")


def plain(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def split(line_en):
    """'<b>Lead.</b> rest <a href="#x">Label</a>' -> (lead, rest) without the link label"""
    s = re.sub(r"\s*<a [^>]*>.*?</a>\s*", " ", line_en).strip()
    m = re.match(r"\s*<b>(.*?)</b>\s*(.*)", s, re.S)
    return (plain(m.group(1)), plain(m.group(2))) if m else ("", plain(s))


def order(brief):
    n = len(brief["lines"])
    o = ((brief.get("x") or {}).get("order") or [])
    if sorted(o) == list(range(1, n + 1)):
        return [i - 1 for i in o]
    def score(i):
        l = brief["lines"][i]
        return PAGE_SCORE.get(l.get("href", "#").lstrip("#"), 3) - (3 if KOREA.search(plain(l["en"])) else 0)
    return sorted(range(n), key=lambda i: (-score(i), i))


def text_of(brief, idx, link=True):
    d = dt.date.fromisoformat(brief["date"])
    head = f"Today in 3 lines · {d.strftime('%b')} {d.day}"
    lead, rest = split(brief["lines"][idx[0]]["en"])
    hook = (brief.get("x") or {}).get("hook") or (lead + " " + rest).strip()
    tail = "\n\n" + URL if link else ""
    budget = 280 - len(head) - 2 - (25 if link else 0)      # a URL counts as 23 + the blank line
    if len(hook) > budget:                                   # cut at a sentence end, else at a word
        cut = hook[:budget]
        m = list(re.finditer(r"[.!?](?=\s|$)", cut))
        hook = cut[:m[-1].end()] if m and m[-1].end() > 40 else cut[:cut.rfind(" ")].rstrip(",;:") + "…"
    return f"{head}\n\n{hook}{tail}"


# ---------- card ----------
def card(brief, idx, out):
    from PIL import Image, ImageDraw, ImageFont
    cands = {"b": ["/usr/share/fonts/opentype/inter/Inter-Bold.otf", "/usr/share/fonts/truetype/inter/Inter-Bold.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
             "r": ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "/usr/share/fonts/truetype/inter/Inter-Regular.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
             "x": ["/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]}
    def F(k, s):
        for p in cands[k]:
            if os.path.exists(p):
                return ImageFont.truetype(p, s)
        return ImageFont.load_default(s)
    W, H = 1600, 900
    BG, PANEL, OR, FG, SUB, MUT = "#0e1726", "#15213b", "#f26422", "#ffffff", "#c9d2e0", "#8e9bb2"
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    dte = dt.date.fromisoformat(brief["date"])
    d.text((90, 70), "TODAY IN 3 LINES", font=F("b", 30), fill=OR)
    ds = f"{dte.strftime('%a')}, {dte.strftime('%b')} {dte.day}, {dte.year}"
    d.text((W - 90, 70), ds, font=F("r", 30), fill=MUT, anchor="ra")
    px0, py0, px1, py1 = 90, 150, W - 90, H - 130
    d.rounded_rectangle((px0, py0, px1, py1), 26, fill=PANEL)
    d.rounded_rectangle((px0, py0, px0 + 10, py1), 5, fill=OR)
    items = [split(brief["lines"][i]["en"]) for i in idx]
    tx, maxw = px0 + 130, px1 - 60 - (px0 + 130)

    def wrap(words, fonts):
        """words: [(text, key)] -> lines of [(text, key)] fitting maxw"""
        lines, cur, w = [], [], 0.0
        for t, k in words:
            ww = fonts[k].getlength(t + " ")
            if cur and w + fonts[k].getlength(t) > maxw:
                lines.append(cur); cur, w = [], 0.0
            cur.append((t, k)); w += ww
        if cur:
            lines.append(cur)
        return lines

    for size in range(46, 27, -1):                 # largest size at which all three items fit the panel
        fonts = {"b": F("b", size), "r": F("r", size)}
        lh, gap = size * 1.42, size * 0.95
        blocks = [wrap([(w, "b") for w in lead.split()] + [(w, "r") for w in rest.split()], fonts) for lead, rest in items]
        total = sum(len(b) for b in blocks) * lh + gap * (len(blocks) - 1)
        if total <= (py1 - py0) - 110:
            break
    y = py0 + ((py1 - py0) - total) / 2
    for n, b in enumerate(blocks, 1):
        d.text((px0 + 60, y), f"{n}.", font=F("x", size), fill=OR)
        for ln in b:
            x = tx
            for t, k in ln:
                d.text((x, y), t, font=fonts[k], fill=FG if k == "b" else SUB)
                x += fonts[k].getlength(t + " ")
            y += lh
        y += gap
    d.ellipse((90, H - 84, 112, H - 62), fill=OR)
    d.text((128, H - 73), "stayhungryasi.com", font=F("b", 32), fill=FG, anchor="lm")
    d.text((W - 90, H - 73), "Public data only. Not investment advice.", font=F("r", 24), fill=MUT, anchor="rm")
    im.save(out, "PNG", optimize=True)
    return out


# ---------- X API (OAuth 1.0a user context; JSON bodies are not part of the signature) ----------
def oauth_header(method, url, k):
    p = {"oauth_consumer_key": k["X_API_KEY"], "oauth_nonce": secrets.token_hex(16), "oauth_signature_method": "HMAC-SHA1",
         "oauth_timestamp": str(int(time.time())), "oauth_token": k["X_ACCESS_TOKEN"], "oauth_version": "1.0"}
    q = lambda s: urllib.parse.quote(str(s), safe="~-._")
    base = "&".join([method, q(url), q("&".join(f"{q(a)}={q(b)}" for a, b in sorted(p.items())))])
    key = f"{q(k['X_API_SECRET'])}&{q(k['X_ACCESS_SECRET'])}"
    p["oauth_signature"] = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{q(a)}="{q(b)}"' for a, b in sorted(p.items()))


def call(url, body, k):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                               headers={"Authorization": oauth_header("POST", url, k), "Content-Type": "application/json",
                                        "User-Agent": "stayhungryasi-xpost"})
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.loads(f.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"X API {e.code} on {url.rsplit('/', 2)[-2:]}: {e.read().decode()[:600]}")


def main():
    dry = "--dry" in sys.argv
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "x-card.png"
    brief = json.loads((ROOT / "data" / "brief.json").read_text(encoding="utf-8"))
    today = dt.datetime.now(KST).date().isoformat()
    force = os.environ.get("XPOST_ANY_DATE") == "1" and dry
    if brief.get("date") != today and not force:
        print(f"skip: brief is for {brief.get('date')}, today is {today} KST"); return
    state_p = ROOT / "live" / "x-post.json"
    state = json.loads(state_p.read_text(encoding="utf-8")) if state_p.exists() else {}
    if state.get("date") == brief["date"] and not dry:
        print(f"skip: already posted for {brief['date']}: {state.get('url')}"); return
    idx = order(brief)
    link = os.environ.get("LINK", "1") != "0"
    text = text_of(brief, idx, link)
    m = FORBIDDEN.search(text + " " + " ".join(plain(l["en"]) for l in brief["lines"]))
    if m:
        sys.exit(f'not posted: forbidden wording "{m.group(0)}"')
    card(brief, idx, out)
    print("order:", [i + 1 for i in idx]); print("--- text", f"({len(text)} chars; a URL counts as 23)"); print(text); print("--- card:", out)
    k = {n: os.environ.get(n, "") for n in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")}
    if dry:
        print("dry run: nothing posted"); return
    if not all(k.values()):
        sys.exit("not posted: X secrets are missing (" + ", ".join(n for n, v in k.items() if not v) + ")")
    media = call("https://api.x.com/2/media/upload",
                 {"media": base64.b64encode(Path(out).read_bytes()).decode(), "media_category": "tweet_image"}, k)
    mid = (media.get("data") or {}).get("id")
    if not mid:
        sys.exit(f"media upload gave no id: {json.dumps(media)[:400]}")
    post = call("https://api.x.com/2/tweets", {"text": text, "media": {"media_ids": [str(mid)]}}, k)
    pid = (post.get("data") or {}).get("id")
    if not pid:
        sys.exit(f"post gave no id: {json.dumps(post)[:400]}")
    rec = dict(kind="x-post", date=brief["date"], posted_kst=dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M"), id=pid,
               url=f"https://x.com/i/status/{pid}", text=text, order=[i + 1 for i in idx], credit="stayhungryasi.com")
    state_p.write_text(json.dumps(rec, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("posted:", rec["url"])


if __name__ == "__main__":
    main()
