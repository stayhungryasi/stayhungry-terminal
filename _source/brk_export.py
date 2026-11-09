#!/usr/bin/env python3
"""
brk_export.py: Berkshire probe (univertrix.com) -> hub live files
=================================================================
The hub does not run the probe and does not re-judge anything. It reads the
universe-dominator repo (univertrix.com) and asks universe-dominator's own
builder (scripts/brk_cockpit.export) for the same data its observatory shows
on the "Berkshire Probe" tab, in ko / en / es / ja:

  live/brk-{ko,en,es,ja}.json   what the hub BERKSHIRE page loads (one language each)
  data/berkshire.json           open data API, all four languages

Translations come from universe-dominator's translation cache (only text that
passed its number, term, compliance and link gates). Untranslated text stays
Korean and the hub marks it "KO".

If the builder's shape changes in a way this file does not understand, or a
privacy term appears, the export fails loudly and the hub keeps the last good files.

Usage: python3 _source/brk_export.py --ud <universe-dominator checkout> --out <hub root>
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
LANGS = ("ko", "en", "es", "ja")
# Same list as _source/agent_export.py / research.py: nothing about the author's employer, name, clients or internal reviews.
FORBIDDEN = re.compile(r'하나증권|Centerfield|김광모|광모|대표님|필승|PB 활용|고객 설명|고객용|고객 성향|내부 투자검토|투자위원회|등록 투자자문|Investment Committee|예시 비중|분할 매수|매수할 기회|분할로 사면')
NEED = ("run", "delta", "price", "band", "scen", "rules", "axes", "milestones", "triggers", "tiles", "disruption", "labels", "links")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ud", required=True, help="universe-dominator checkout")
    ap.add_argument("--out", required=True, help="hub repo root")
    a = ap.parse_args()
    ud, out = Path(a.ud).resolve(), Path(a.out).resolve()
    sys.path.insert(0, str(ud / "scripts"))
    try:
        import brk_cockpit as bc   # noqa: E402  (universe-dominator)
    except Exception as e:
        sys.exit(f"[brk_export] universe-dominator has no brk_cockpit ({e}) - nothing written")
    try:
        sha = subprocess.run(["git", "-C", str(ud), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:
        sha = ""
    meta = {"source": "universe-dominator/agent-research/berkshire (univertrix.com)", "commit": sha[:12],
            "generated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"), "credit": "stayhungryasi.com"}
    per = {}
    for lang in LANGS:
        d = bc.export(lang)
        miss = [k for k in NEED if k not in (d or {})]
        if miss:
            sys.exit(f"[brk_export] {lang}: builder shape changed, missing {miss} - nothing written")
        if not d["milestones"] or not d["run"].get("id"):
            sys.exit(f"[brk_export] {lang}: empty cockpit - nothing written")
        m = FORBIDDEN.search(json.dumps(d, ensure_ascii=False))
        if m:
            sys.exit(f"[brk_export] privacy check failed in {lang}: {m.group(0)!r} - nothing written")
        per[lang] = d
    # content hash ignores the generation time so an unchanged probe makes no commit
    h = hashlib.sha1(json.dumps(per, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    meta["hash"] = h
    (out / "live").mkdir(exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    try:
        prev = json.loads((out / "data" / "berkshire.json").read_text(encoding="utf-8")).get("meta", {})
    except Exception:
        prev = {}
    if prev.get("hash") == h:
        print(f"[brk_export] unchanged ({h}), run {per['ko']['run']['id']}")
        return
    for lang in LANGS:
        doc = dict(meta=meta, **per[lang])
        (out / "live" / f"brk-{lang}.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    api = {"meta": dict(meta, note="Berkshire Hathaway probe: the same cockpit univertrix.com shows (run, what changed, price vs "
                                   "assumed value band, scenarios, milestones by axis, triggers, probability rules, KPIs, "
                                   "disruption watch, SEC filings, latest report), in ko/en/es/ja under langs. Synced every 3 hours. "
                                   "Machine-generated assumptions, not investment advice, not a price target."),
           "langs": per}
    (out / "data" / "berkshire.json").write_text(json.dumps(api, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    sizes = {lang: (out / "live" / f"brk-{lang}.json").stat().st_size // 1024 for lang in LANGS}
    print(f"[brk_export] wrote run {per['ko']['run']['id']} · hash {h} · KB {sizes}")


if __name__ == "__main__":
    main()
