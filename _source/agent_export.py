#!/usr/bin/env python3
"""
agent_export.py: SpaceX overnight research agent -> hub live files
==================================================================
The hub does not run the agent and does not re-judge anything. It reads the
universe-dominator repo (univertrix.com), asks universe-dominator's own cockpit
builder (scripts/probe_cockpit.build) for the same data its observatory shows,
in ko / en / es / ja, and keeps a compact subset:

  live/agent-{ko,en,es,ja}.json   what the hub page loads (one language each)
  data/agent.json                 open data API, all four languages

Translations come from universe-dominator's translation cache, which only holds
text that passed its gates (numbers, terms, compliance, links). Text that is
not translated yet stays Korean and the hub marks it "KO".

Because the hub calls universe-dominator's own builder, every upgrade made
there (new milestones, rules, report sections, translations) flows here on the
next sync without changing this file. If the builder's shape changes in a way
this file does not understand, the export fails loudly and the hub keeps the
last good files.

Usage: python3 _source/agent_export.py --ud <universe-dominator checkout> --out <hub root>
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
UV = "https://univertrix.com/"
# Same list as _source/research.py: nothing about the author's employer, name, clients or internal reviews.
FORBIDDEN = re.compile(r'하나증권|Centerfield|김광모|광모|대표님|필승|PB 활용|고객 설명|고객용|고객 성향|내부 투자검토|투자위원회|등록 투자자문|Investment Committee|예시 비중|분할 매수|매수할 기회|분할로 사면')
ST_KEYS = ("done", "early", "met", "prog", "miss", "wait")


def uv_url(lang, page, anchor=""):
    base = UV + ("" if lang == "ko" else lang + "/")
    return base + page + (("#" + anchor) if anchor else "")


def abs_url(lang, u):
    if not u:
        return ""
    if re.match(r"https?://", u):
        return u
    page, _, anc = u.partition("#")
    return uv_url(lang, page.lstrip("/"), anc)


def pick(d, *keys):
    return {k: d.get(k) for k in keys if k in d}


def build_lang(pc, ar, i18n, lang):
    d, reports = pc.build(ar, lang=lang)
    t = lambda k, **p: i18n.t(lang, k, **p)
    run = d["run"]
    out = {
        "lang": lang,
        "run": pick(run, "id", "date", "mode", "number", "prev", "engine", "engineOk", "engineDate",
                    "verify", "next", "overdue", "stale", "age"),
        "delta": [{"id": x.get("id"), "kind": x.get("kind"), "lines": x.get("lines") or []} for x in d["delta"]],
        "price": d["price"],
        "band": pick(d["band"], "lo", "hi", "mid", "pw", "rate"),
        "scen": [dict(pick(s, "key", "prob", "prev", "vps", "rationale"), label=s.get("ko")) for s in d["scen"]],
        "rules": d["rules"],
        "proposals": d["proposals"],
        "history": [pick(h, "run_id", "run_date", "price", "price_date", "probs", "band", "mid", "pw_value")
                    for h in d["history"]],
        "axes": [dict(pick(a, "key", "n", "measured", "avg", "met"), label=a.get("ko"),
                      counts={pc.SHOWN_CLS.get(k, k): v for k, v in (a.get("counts") or {}).items()})
                 for a in d["axes"]],
        "milestones": [dict(pick(m, "id", "axis", "year", "text", "cls", "pct", "cur", "tgt", "unit", "asof",
                                 "source", "reason", "hit", "miss", "method"),
                            axisL=m.get("axisKo"),
                            hist=[h.get("cls") for h in (m.get("history") or [])])
                       for m in d["milestones"]],
        "triggers": [pick(x, "id", "name", "expected", "statusL", "when", "dday", "note", "prev") for x in d["triggers"]],
        "events": [dict(pick(e, "id", "date", "kind", "title", "source", "form"), kindL=e.get("kindKo"),
                        url=abs_url(lang, e.get("url"))) for e in d["events"][:12]],
        "tiles": [pick(x, "id", "label", "value", "q", "dir", "series") for x in d["tiles"]],
        "feeds": d["feeds"],
        "reports": [{"id": r.get("id"), "title": r.get("title"), "n": len(r.get("sections") or [])} for r in reports],
        "report": None,
        "labels": {
            "st": {k: t("pc.st." + k) for k in ST_KEYS},
            "scen": {k: t("pc.scen." + k) for k in ("bull", "base", "bear")},
            "disclaimer": t("pc.disclaimer"),
        },
        "links": {
            "observatory": uv_url(lang, "observatory.html", "probe"),
            "home": uv_url(lang, "index.html"),
            "repo": "https://github.com/stayhungryasi/universe-dominator/tree/main/agent-research",
        },
    }
    if reports:
        r = reports[0]
        out["report"] = {"id": r.get("id"), "title": r.get("title"),
                         "sections": [{"id": s.get("id"), "title": s.get("toc") or s.get("title"), "html": s.get("html")}
                                      for s in (r.get("sections") or [])]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ud", required=True, help="universe-dominator checkout")
    ap.add_argument("--out", required=True, help="hub repo root")
    a = ap.parse_args()
    ud, out = Path(a.ud).resolve(), Path(a.out).resolve()
    sys.path.insert(0, str(ud / "scripts"))
    import agent_report as ar      # noqa: E402  (universe-dominator)
    import i18n                    # noqa: E402
    import probe_cockpit as pc     # noqa: E402

    try:
        sha = subprocess.run(["git", "-C", str(ud), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:
        sha = ""
    meta = {"source": "universe-dominator/agent-research (univertrix.com)", "commit": sha[:12],
            "generated_at": datetime.now(KST).strftime("%Y-%m-%d %H:%M KST"),
            "credit": "@stayhungryasi · https://t.me/stayhungryasi"}
    per = {}
    for lang in LANGS:
        per[lang] = build_lang(pc, ar, i18n, lang)
        blob = json.dumps(per[lang], ensure_ascii=False)
        m = FORBIDDEN.search(blob)
        if m:
            sys.exit(f"[agent_export] privacy check failed in {lang}: {m.group(0)!r} - nothing written")
        if not per[lang]["milestones"] or not per[lang]["run"].get("id"):
            sys.exit(f"[agent_export] {lang}: empty cockpit - nothing written")

    # content hash ignores the generation time so an unchanged agent makes no commit
    h = hashlib.sha1(json.dumps(per, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    meta["hash"] = h
    (out / "live").mkdir(exist_ok=True)
    (out / "data").mkdir(exist_ok=True)
    prev = {}
    try:
        prev = json.loads((out / "data" / "agent.json").read_text(encoding="utf-8")).get("meta", {})
    except Exception:
        pass
    if prev.get("hash") == h:
        print(f"[agent_export] unchanged ({h}), run {per['ko']['run']['id']}")
        return
    for lang in LANGS:
        doc = dict(meta=meta, **per[lang])
        (out / "live" / f"agent-{lang}.json").write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    api = {"meta": dict(meta, note="SpaceX overnight research agent: the same cockpit univertrix.com shows, in 4 languages. "
                                   "Machine-generated assumptions, not investment advice, not a price target."),
           "langs": {lang: per[lang] for lang in LANGS}}
    (out / "data" / "agent.json").write_text(json.dumps(api, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    sizes = {lang: (out / "live" / f"agent-{lang}.json").stat().st_size // 1024 for lang in LANGS}
    print(f"[agent_export] wrote run {per['ko']['run']['id']} · hash {h} · KB {sizes}")


if __name__ == "__main__":
    main()
