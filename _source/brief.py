#!/usr/bin/env python3
"""Daily brief (TODAY + BRIEF pages) for stayhungryasi.com

  python3 _source/brief.py digest             # what every live feed says right now (read this, then pick)
  python3 _source/brief.py publish draft.json  # check the pick and write live/brief.json, data/brief.json, data/brief-history.json

draft.json:
{
  "lines": [ {"href": "#spcxlock", "ko": "...", "en": "...", "es": "...", "ja": "..."}, x3 ],
  "checkpoints": [ {"d": {"ko": "10/26(월)", ...}, "x": {...}, "y": {...}}, up to 3 ],
  "why": {"ko": "...", "en": "...", "es": "...", "ja": "..."},
  "facts": ["every number used, with the feed it came from", ...]
}
Lines may use only <b>…</b> and <a href="#page">…</a> (hub pages). Pure public data: no affiliation, client,
internal-review or buy/sell wording (same rule as the research library). Run from the repo root.
@stayhungryasi · https://t.me/stayhungryasi
"""
import datetime as dt, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KST = dt.timezone(dt.timedelta(hours=9))
LANGS = ("ko", "en", "es", "ja")
PAGES = {"today", "brief", "earnings", "schedule", "research", "mix", "score", "spcxlock", "library", "radar",
         "rank", "univertrix", "uvmap", "lab", "brains", "hub", "news", "buffett", "vix", "fear"}
TAG = re.compile(r"<(?!/?b>|a href=\"#[a-z]+\">|/a>)[^>]*>")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from research import FORBIDDEN  # noqa: E402


def load(p):
    f = ROOT / p
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def today():
    return dt.datetime.now(KST).date()


def digest():
    d0 = today()
    print(f"# Hub digest · {d0} KST\n")
    cr = load("live/crisis.json")
    if cr:
        reds = [i for i in cr["indicators"] if i.get("sig") == "R"]
        print(f"## Crisis bot (#radar) · report {cr.get('sent_kst') or cr.get('report_kst')}")
        print(f"- score {cr['score']} ({cr['regime']}), previous {(cr.get('prev') or {}).get('score')} · red {len(reds)}: "
              + ", ".join(i['key'] for i in reds))
        print("- layers: " + ", ".join(f"{l['id']} {l['score']}" for l in cr["layers"]))
    fr = load("live/fear.json")
    if fr and fr.get("buffett"):
        b, v = fr["buffett"], fr.get("vix") or {}
        print(f"\n## Buffett Index x VIX (#radar, #buffett) · {'sent ' + str(fr.get('sent_kst')) if fr.get('sent') else 'check run ' + str(fr.get('run_kst'))}")
        print(f"- Buffett {b.get('value')}% ({b.get('key')}, pct {b.get('pct')}, estimated={b.get('estimated')}, official {b.get('last_official')} {b.get('official_quarter')})")
        print(f"- VIX {v.get('value')} ({v.get('key')}, as of {v.get('asof')}, 1w {v.get('d1w')}, 1m {v.get('d1m')}, VIX/VIX3M {v.get('ratio')})")
    lk = load("live/spcx-lock.json")
    if lk and lk.get("next"):
        n, s = lk["next"], lk["summary"]
        print(f"\n## SpaceX lock-up radar (#spcxlock) · asof {lk['asof']}")
        print(f"- next: {n['label']} · trade {n['trade']} (contract {n['contract_date']}) · D-{n['dday']} · {n['shares_m']}M shares "
              f"· +{n.get('vs_eligible_pct')}% vs tradable · ≈${n.get('usd_b')}B")
        print(f"- tradable {s['eligible_pct']}% · locked {s['locked_m']}M ({s['locked_pct']}%) · year-end {s['yearend_pct']}%")
        if lk.get("price"):
            p = lk["price"]
            print(f"- SPCX ${p['last']} ({p['last_date']} close, {p['chg_pct']:+}% d/d, {p['vs_ipo_pct']:+}% vs IPO $135)")
    sc = load("live/schedule.json")
    if sc:
        print(f"\n## Key dates bot (#schedule) · data {sc.get('data_updated')} · last Telegram {sc.get('last_sent_kst')}")
        lo, hi = d0.isoformat(), (d0 + dt.timedelta(days=7)).isoformat()
        for e in sc["events"]:
            if lo <= e["date"] <= hi and e["imp"] >= 2:
                print(f"- {e['date']} {e['time'] or '     '} KST {'★' if e['imp'] >= 3 else ' '} {e['title']} [{e['status']}] ({e['cat']})")
        ch = [e for e in sc["events"] if e.get("change") and e.get("updated", "") >= (d0 - dt.timedelta(days=4)).isoformat()]
        for e in ch:
            print(f"- CHANGED {e['date']} {e['title']}: {e['change']}")
    rs = load("data/research.json")
    if rs:
        print("\n## Research library (#library)")
        for r in rs["reports"][:3]:
            print(f"- {r['date']} {r['title']['ko']} · key {r['key']['value']} · {r['url']}")
    cl = load("data/changelog.json")
    if cl:
        print("\n## Site changelog (#news)")
        for c in cl["items"][:3]:
            print(f"- {c['date']} {c['message']}")
    prev = load("data/brief-history.json") or []
    if prev:
        print("\n## Previous briefs (avoid repeating a line unless it is still the most important thing)")
        for b in prev[-3:][::-1]:
            print(f"- {b['date']}: " + " | ".join(re.sub(r'<[^>]+>', '', l['ko']) for l in b['lines']))


def publish(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    errs = []
    lines = d.get("lines") or []
    if len(lines) != 3:
        errs.append("need exactly 3 lines")
    for i, l in enumerate(lines):
        if l.get("href", "#").lstrip("#") not in PAGES:
            errs.append(f"line {i + 1}: href {l.get('href')} is not a hub page")
        for c in LANGS:
            v = l.get(c, "")
            if not v.strip():
                errs.append(f"line {i + 1}: {c} missing")
            if TAG.search(v):
                errs.append(f"line {i + 1} {c}: only <b> and <a href=\"#page\"> allowed")
            for h in re.findall(r'href="#([a-z]+)"', v):
                if h not in PAGES:
                    errs.append(f"line {i + 1} {c}: unknown page #{h}")
            if len(re.sub(r"<[^>]+>", "", v)) > 140:
                errs.append(f"line {i + 1} {c}: longer than 140 characters")
    for c in LANGS:
        if not (d.get("why") or {}).get(c):
            errs.append(f"why.{c} missing")
    blob = json.dumps(d, ensure_ascii=False)
    m = FORBIDDEN.search(blob)
    if m:
        errs.append(f'forbidden wording "{m.group(0)}" (public, pure research and data only)')
    if errs:
        sys.exit("brief NOT published:\n- " + "\n- ".join(errs))
    now = dt.datetime.now(KST)
    doc = dict(kind="brief", schema=1, date=today().isoformat(), generated_kst=now.strftime("%Y-%m-%d %H:%M"),
               editor="Claude", lines=lines, checkpoints=(d.get("checkpoints") or [])[:3], why=d["why"],
               facts=d.get("facts") or [], credit="@stayhungryasi · https://t.me/stayhungryasi",
               note="Picked from the hub's live feeds. Not investment advice.")
    (ROOT / "live").mkdir(exist_ok=True)
    (ROOT / "live" / "brief.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (ROOT / "data" / "brief.json").write_text(json.dumps(dict(doc, live="https://stayhungryasi.com/live/brief.json"),
                                                         ensure_ascii=False, indent=1), encoding="utf-8")
    hp = ROOT / "data" / "brief-history.json"
    hist = json.loads(hp.read_text(encoding="utf-8")) if hp.exists() else []
    hist = [h for h in hist if h["date"] != doc["date"]] + [dict(date=doc["date"], lines=lines, why=doc["why"])]
    hp.write_text(json.dumps(hist[-90:], ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"brief published for {doc['date']}: " + " | ".join(re.sub(r'<[^>]+>', '', l['ko']) for l in lines))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "digest":
        digest()
    elif len(sys.argv) >= 3 and sys.argv[1] == "publish":
        publish(sys.argv[2])
    else:
        sys.exit(__doc__)
