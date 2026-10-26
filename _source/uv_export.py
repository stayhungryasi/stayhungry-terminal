#!/usr/bin/env python3
"""
uv_export.py: univertrix.com (universe-dominator) market data -> hub live files
===============================================================================
Two hub pages run on universe-dominator's own daily data. The hub only reshapes it:

  live/rank.json      global market-cap Top 20, every daily snapshot since the first one
                      (rank and market cap per company per day) -> RANK page (#rank)
  live/earnings.json  earnings dates of the companies in that Top 20, from universe-dominator's
                      calendar (Finnhub), plus the ones already reported (kept 45 days)
                      -> EARNINGS page (#earnings)
  data/rank.json, data/earnings.json   the same, for the open data API

The page computes month-end ranks, entries and exits, streaks and post-earnings
moves itself, so a new snapshot is all it needs. No trading rules are published.

Usage: python3 _source/uv_export.py --ud <universe-dominator checkout> --out <hub root>
"""
import argparse
import hashlib
import json
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
LANGS = ("ko", "en", "es", "ja")
KEEP_PAST_DAYS = 45


def read(p, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


def write(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def h12(obj):
    return hashlib.sha1(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ud", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ud, out = Path(a.ud).resolve(), Path(a.out).resolve()
    (out / "live").mkdir(exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    sha = subprocess.run(["git", "-C", str(ud), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()[:12]
    now = datetime.now(KST)
    names_i18n = read(ud / "data/i18n/names.json", {}) or {}
    latest = read(ud / "data/latest.json", {}) or {}
    flags = {s.get("ticker"): s.get("flag", "") for s in ((latest.get("regions") or {}).get("earth") or {}).get("stocks", [])}

    # ---------------- rank ----------------
    snaps = sorted((ud / "data/snapshots").glob("*.json"))
    days, rank, mc, name = [], {}, {}, {}
    for f in snaps:
        d = read(f, {}) or {}
        rows = ((d.get("regions") or {}).get("earth")) or []
        if len(rows) < 10:
            continue
        i = len(days)
        days.append(d.get("date") or f.stem)
        for r in rows:
            tk = r.get("ticker")
            if not tk:
                continue
            name.setdefault(tk, r.get("name") or tk)
            name[tk] = r.get("name") or name[tk]
            rank.setdefault(tk, [None] * i)
            mc.setdefault(tk, [None] * i)
            rank[tk].append(r.get("rank"))
            mc[tk].append(r.get("mc"))
        for tk in rank:
            if len(rank[tk]) < i + 1:
                rank[tk].append(None)
                mc[tk].append(None)
    if len(days) < 2:
        raise SystemExit("[uv_export] not enough snapshots - nothing written")

    def names_for(tk, nm):
        n = names_i18n.get(tk) or {}
        return {l: n.get(l) or nm for l in LANGS}

    tickers = [{"tk": tk, "name": names_for(tk, name[tk]), "flag": flags.get(tk, "")} for tk in rank]
    rank_doc = {"kind": "rank", "schema": 1, "universe": "earth", "unit": "USD billions",
                "asof": days[-1], "first": days[0], "days": days, "tickers": tickers, "rank": rank, "mc": mc}

    # ---------------- earnings ----------------
    cal = read(ud / "data/calendar.json", {}) or {}
    today = now.date().isoformat()
    ever = set(rank)
    items = []
    for e in cal.get("events") or []:
        if e.get("type") != "earnings" or e.get("ticker") not in ever:
            continue
        tk = e["ticker"]
        items.append({"t": tk, "date": e.get("date"), "hour": e.get("hour") or "",
                      "name": names_for(tk, e.get("name") or name.get(tk, tk))})
    prev = read(out / "live/earnings.json", {}) or {}
    cut = (now.date() - timedelta(days=KEEP_PAST_DAYS)).isoformat()
    past = {(x["t"], x["date"]): x for x in (prev.get("past") or []) if x.get("date", "") >= cut}
    for x in (prev.get("items") or []):           # yesterday's upcoming that are now in the past
        if cut <= x.get("date", "") < today:
            past[(x["t"], x["date"])] = x
    for x in items:
        if x["date"] < today:
            past[(x["t"], x["date"])] = x
    items = sorted([x for x in items if x["date"] >= today], key=lambda x: (x["date"], x["t"]))
    seen = {x["t"] for x in items}
    # a calendar date that moved later (estimate revised) is not a report: drop past rows whose
    # company has an upcoming date within 30 days, and keep one row per company per 30 days
    def near(d1, d2):
        return abs((date.fromisoformat(d1) - date.fromisoformat(d2)).days) <= 30
    clean = []
    for x in sorted(past.values(), key=lambda x: x["date"], reverse=True):
        if any(u["t"] == x["t"] and near(u["date"], x["date"]) for u in items):
            continue
        if any(c["t"] == x["t"] and near(c["date"], x["date"]) for c in clean):
            continue
        x["name"] = names_for(x["t"], name.get(x["t"]) or (x.get("name") or {}).get("en") or x["t"])
        clean.append(x)
    earn_doc = {"kind": "earnings", "schema": 1, "universe": "earth Top 20",
                "calendar_generated": cal.get("generated_at"), "items": items,
                "past": clean,
                "no_date": [tk for tk in rank if rank[tk][-1] is not None and tk not in seen]}

    for nm, doc in (("rank", rank_doc), ("earnings", earn_doc)):
        hh = h12(doc)
        old = read(out / "live" / f"{nm}.json", {}) or {}
        if (old.get("meta") or {}).get("hash") == hh:
            print(f"[uv_export] {nm}: unchanged ({hh})")
            continue
        doc = dict(meta={"source": "univertrix.com (universe-dominator: daily market-cap snapshots, calendar via Finnhub)",
                         "commit": sha, "generated_at": now.strftime("%Y-%m-%d %H:%M KST"), "hash": hh,
                         "credit": "@stayhungryasi · https://t.me/stayhungryasi",
                         "note": "Market data and dates only. Not investment advice."}, **doc)
        write(out / "live" / f"{nm}.json", doc)
        write(out / "data" / f"{nm}.json", doc)
        print(f"[uv_export] {nm}: wrote {hh} · " + (f"{len(days)} days, {len(rank)} companies" if nm == "rank"
                                                    else f"{len(items)} upcoming, {len(earn_doc['past'])} past"))


if __name__ == "__main__":
    main()
