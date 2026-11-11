"""Write the hub's AI-models summary from data6.json. Every number comes from the data.
Outputs (same content): <repo>/live/models.json (read by the reader page) and <repo>/data/models.json (open data API).
usage: python3 make_live.py <repo root>"""
import json, sys, datetime
d = json.load(open("data6.json", encoding="utf-8"))
R, C = d["rows"], d["cells"]
T = [t["id"] for t in d["tasks"]]
M = {m["id"]: m for m in d["models"]}

def combo(m, l, with_tasks=False):
    r = R[m][l]
    o = {"id": m, "model": M[m]["label"], "vendor": M[m]["vendor"], "level": l, "index": r["ii"],
         "cost_usd": r["cost"], "minutes": round(r["time"] / 60, 1) if r.get("time") else None}
    if with_tasks: o["tasks"] = C[m][l]["s"]
    return o

allc = [(m, l) for m in R for l in R[m]]
lead = max(allc, key=lambda x: R[x[0]][x[1]]["ii"])
ref = ("fable51", "xhigh")
cands = [(m, l) for m, l in allc if M[m]["group"] in ("claude", "claudeold") and C[m][l]["cost"] is not None
         and all(C[m][l]["s"][t] >= C[ref[0]][ref[1]]["s"][t] for t in T)]
to = min(cands, key=lambda x: C[x[0]][x[1]]["cost"])
outside = max(((m, l) for m, l in allc if M[m]["vendor"] != "Anthropic"), key=lambda x: R[x[0]][x[1]]["ii"])
cheap = min(((m, l) for m, l in allc if R[m][l]["ii"] >= 55 and R[m][l]["cost"] is not None), key=lambda x: R[x[0]][x[1]]["cost"])
openw = max(((m, l) for m, l in allc if M[m]["open"]), key=lambda x: R[x[0]][x[1]]["ii"])
best_lv = {m: max(R[m], key=lambda l: (R[m][l]["ii"], -(R[m][l]["cost"] or 1e9))) for m in R}
top = sorted(best_lv.items(), key=lambda x: -R[x[0]][x[1]]["ii"])[:10]
asof = datetime.date.fromisoformat(d["asof"])
def rel(m):
    try: return datetime.date.fromisoformat(M[m]["release"])
    except ValueError: return None
new = sorted((m for m in M if rel(m) and (asof - rel(m)).days <= 45), key=lambda m: rel(m), reverse=True)
out = {
 "asof": d["asof"], "ruler": "Artificial Analysis Intelligence Index v5.0.1", "update": "monthly",
 "page": "https://stayhungryasi.com/p/ai-models/",
 "n_models": len(M), "n_combos": sum(len(v) for v in C.values()),
 "leader": combo(*lead),
 "switch": {"from": combo(*ref), "to": combo(*to), "cost_pct": round(C[to[0]][to[1]]["cost"] / C[ref[0]][ref[1]]["cost"] * 100),
            "higher_on_all_tasks": True},
 "outside_anthropic": combo(*outside), "cheapest_index_55": combo(*cheap), "open_weights": combo(*openw),
 "top": [combo(m, l) for m, l in top],
 "tasks": [{"id": t["id"], "name_ko": t["name"], "weights": t["weights"],
            "top": dict(combo(*d["recs"]["all"][t["id"]]["topCombo"]), score=d["recs"]["all"][t["id"]]["top"]),
            "value_all": combo(*d["recs"]["all"][t["id"]]["value"]),
            "value_claude": combo(*d["recs"]["claude"][t["id"]]["value"])} for t in d["tasks"]],
 "new": [{"id": m, "model": M[m]["label"], "vendor": M[m]["vendor"], "release": M[m]["release"]} for m in new],
 "notes": {"scores": "Task scores (0-10) are the author's estimate: a weighted mix of AA benchmarks. Index, cost and time are read from Artificial Analysis.",
           "value": "value = cheapest combination within 90% of the best task score; levels: low, medium, high, xhigh, max."},
 "source": "https://artificialanalysis.ai/", "credit": "stayhungryasi.com",
}
root = sys.argv[1]
for p in ("live/models.json", "data/models.json"):
    json.dump(out, open(f"{root}/{p}", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("asof", "n_models", "n_combos", "leader", "switch")}, ensure_ascii=False)[:700])
