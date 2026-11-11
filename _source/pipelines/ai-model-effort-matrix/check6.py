"""Sanity checks before publishing. Exit code 1 = do NOT publish.
usage: python3 check6.py [hub_app.html] [--prev data6_prev.json]"""
import json, re, sys
from aa_v6 import ROWS, K
try:
    from aa_v6_gpt import GROWS
    ROWS.update(GROWS)
except ImportError:
    pass
errs, warns = [], []
NOCOST = {"musefull"}            # no public API -> no cost/time
for mid, rows in ROWS.items():
    for lv, r in rows.items():
        for k in K:
            if r.get(k) is None: errs.append(f"{mid}/{lv}: missing {k}")
        if not (0 <= r["ii"] <= 100): errs.append(f"{mid}/{lv}: ii out of range {r['ii']}")
        if mid not in NOCOST:
            if r.get("cost") is None: errs.append(f"{mid}/{lv}: missing cost")
            if r.get("time") is None: warns.append(f"{mid}/{lv}: missing time")
        for k in ("auto", "gdppdf", "fc", "tb4", "tbsci", "crit", "hled"):
            if r.get(k) is not None and not (0 <= r[k] <= 100): errs.append(f"{mid}/{lv}: {k} out of range {r[k]}")
        if r.get("brief") is not None and not (500 <= r["brief"] <= 2500): errs.append(f"{mid}/{lv}: brief Elo odd {r['brief']}")
# identical-row smell test (copy/paste or cached-page errors)
sig = {}
for mid, rows in ROWS.items():
    for lv, r in rows.items():
        key = tuple(r[k] for k in K)
        if key in sig: errs.append(f"identical rows: {mid}/{lv} == {sig[key]}")
        sig[key] = f"{mid}/{lv}"
# monotone-ish index within a model (big drops usually mean a stale page)
LV = ["low", "medium", "high", "xhigh", "max"]
for mid, rows in ROWS.items():
    seq = [rows[l]["ii"] for l in LV if l in rows]
    for a, b in zip(seq, seq[1:]):
        if b < a - 3: warns.append(f"{mid}: index drops {a}->{b} between effort levels (check page)")
if "--prev" in sys.argv:
    prev = json.load(open(sys.argv[sys.argv.index("--prev") + 1], encoding="utf-8"))["rows"]
    for mid, rows in ROWS.items():
        for lv, r in rows.items():
            p = prev.get(mid, {}).get(lv)
            if p and abs(p["ii"] - r["ii"]) >= 6: warns.append(f"{mid}/{lv}: index moved {p['ii']} -> {r['ii']} since last run (explain in findings)")
F = re.compile(r"하나증권|Centerfield|김광모|광모|대표님|필승|PB 활용|고객 설명|고객용|고객 성향|내부 투자검토|투자위원회|등록 투자자문|Investment Committee|예시 비중|분할 매수|매수할 기회|분할로 사면|몬스터테크놀로지|VIP")
for a in sys.argv[1:]:
    if a.endswith(".html"):
        hits = sorted(set(F.findall(open(a, encoding="utf-8").read())))
        if hits: errs.append(f"{a}: forbidden terms {hits}")
print("ERRORS:", *errs, sep="\n  ") if errs else print("ERRORS: none")
print("WARNINGS:", *warns, sep="\n  ") if warns else print("WARNINGS: none")
sys.exit(1 if errs else 0)
