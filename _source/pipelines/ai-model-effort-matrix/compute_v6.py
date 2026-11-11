"""v6 (2026-11-11): one yardstick for every model = Artificial Analysis Intelligence Index v5.0.1.
Every scored combo is an AA measurement of that exact model+effort variant. Task scores = weighted mapping [추정]."""
import json, sys
sys.path.insert(0, ".")
from aa_v6 import ROWS, LB_ONLY, K
try:
    from aa_v6_gpt import GROWS
    ROWS.update(GROWS)
except ImportError:
    pass

ASOF = "2026-11-11"
LV = ["low", "medium", "high", "xhigh", "max"]

# id, label, vendor, group, price[in,out], open, release, app default effort (None = n/a), note
META = [
 ("fable52", "Claude Fable 5.2", "Anthropic", "claude", [8, 40], False, "2026-11-09", "medium", "앱·Claude Code 기본 중간, API 기본 높음"),
 ("opus55", "Claude Opus 5.5", "Anthropic", "claude", [4, 20], False, "2026-09-22", "medium", "API 기본 중간"),
 ("sonnet55", "Claude Sonnet 5.5", "Anthropic", "claude", [2, 10], False, "2026-09-28", "medium", "앱 기본 중간, API 기본 높음"),
 ("haiku55", "Claude Haiku 5.5", "Anthropic", "claude", [0.1, 0.5], False, "2026-10-07", "medium", "API 기본 중간, 10만 토큰 이하 단가"),
 ("fable51", "Claude Fable 5.1", "Anthropic", "claudeold", [10, 50], False, "2026-09", "medium", "현재 설정(엑스트라)"),
 ("opus5", "Claude Opus 5", "Anthropic", "claudeold", [5, 25], False, "2026", None, "v5 지수는 최대만 측정"),
 ("astra", "GPT-6 Astra", "OpenAI", "openai", [10, 50], False, "2026-09-03", None, "GPT-6.1 Astra는 출시 취소(보도)"),
 ("sol61", "GPT-6.1 Sol", "OpenAI", "openai", [2, 10], False, "2026-09-29", "medium", "API 기본 중간, ChatGPT는 Work·Codex만"),
 ("terra61", "GPT-6.1 Terra", "OpenAI", "openai", [1, 5], False, "2026-10-26", "medium", "API 기본 중간, ChatGPT는 Work·Codex만"),
 ("sol6", "GPT-6 Sol", "OpenAI", "openai", [2, 10], False, "2026-09-22", None, "10/7부터 ChatGPT 일반 Chat"),
 ("luna", "GPT-6 Luna", "OpenAI", "openai", [0.1, 0.5], False, "2026-09-22", None, "ChatGPT 무료 기본 모델"),
 ("carbon", "Gemini 4 Carbon", "Google", "google", [4, 20], False, "2026-10-28", None, "출시 기념가 $2/$10, 제한 공개"),
 ("argon", "Gemini 4 Argon", "Google", "google", [4, 20], False, "2026-09", None, ""),
 ("flash38", "Gemini 3.8 Flash", "Google", "google", [0.75, 3.75], False, "2026-09", None, ""),
 ("musefull", "Muse Wonder Full", "Meta", "meta", None, False, "2026-10-12", None, "공개 API 없음"),
 ("muse", "Muse Wonder", "Meta", "meta", [4, 20], False, "2026-10", None, ""),
 ("ember", "Muse Ember", "Meta", "meta", [0.1, 0.5], False, "2026-11-09", None, ""),
 ("kimi", "Kimi K3.1 Pro", "Moonshot", "other", [2, 10], True, "2026-10-23", None, "오픈 웨이트 1위"),
 ("grok", "Grok 4.7", "xAI", "other", [2, 6], False, "2026-09", None, ""),
 ("hy4", "Tencent Hy4", "Tencent", "other", [0.83, 2.5], False, "2026-11-03", None, "웨이트 공개 예정"),
 ("qwen", "Qwen3.8 Max", "Alibaba", "other", [2, 6], False, "2026-09", None, ""),
 ("deepseek", "DeepSeek V4.1 Flash", "DeepSeek", "other", [0.3, 1.2], True, "2026-10", None, "1017 버전"),
 ("glm", "GLM-5.3", "Z AI", "other", [1.4, 4.4], True, "2026-08", None, ""),
 ("mimo", "MiMo-V2.6-Pro", "Xiaomi", "other", [0.43, 0.87], True, "2026-09-21", None, ""),
 ("minimax", "MiniMax-M3.1-Flash", "MiniMax", "other", [0.15, 0.6], True, "2026-10", None, ""),
 ("inkling", "Inkling 2 Small", "Thinking Machines", "other", [0.3, 1.0], False, "2026-11-05", None, "웨이트 공개 예정"),
 ("mistral", "Mistral Large 4", "Mistral", "other", [0.7, 2.1], True, "2026-10-29", None, ""),
]
META = [m for m in META if m[0] in ROWS]
MD = {m[0]: m for m in META}

TASKS = [
 ("t1", "시스템 고도화", {"tb4": .35, "fc": .35, "auto": .20, "omni": .10}),
 ("t2", "기업분석",       {"brief": .30, "omni": .25, "gdppdf": .20, "hled": .15, "auto": .10}),
 ("t3", "리서치",         {"omni": .30, "hled": .30, "crit": .15, "brief": .15, "gdppdf": .10}),
 ("t4", "게임 개발",      {"fc": .45, "tb4": .35, "tbsci": .20}),
 ("t5", "프로그램 개발",  {"fc": .40, "tb4": .40, "auto": .20}),
]
BENCH = [  # key, name, unit, why, AA weight in index v5.0.1
 ("brief", "AA-Briefcase (Elo)", "Elo", "실제 지식업무 산출물(보고서·분석) 블라인드 비교", 15),
 ("auto", "AutomationBench-AA", "%", "여러 앱을 잇는 업무 자동화", 5),
 ("gdppdf", "GDP.pdf", "%", "긴 전문 문서(PDF) 읽고 답하기", 5),
 ("fc", "FrontierCode 2.0", "%", "범위 밖 수정 없이 병합 가능한 코드", 15),
 ("tb4", "Terminal-Bench 4.0", "%", "장시간 터미널 에이전트 작업 완수", 10),
 ("tbsci", "Terminal-Bench-Science 0.1", "%", "과학 계산·시뮬레이션 에이전트", 15),
 ("crit", "CritPt v2 (Hard)", "%", "연구 수준 물리 추론", 10),
 ("omni", "AA-Omniscience v1.1", "점", "모르면 모른다고 하는 정도(환각 억제, 순점수)", 15),
 ("hled", "HLE-Diamond", "%", "최고 난도 전문 지식 문제", 10),
]
BK = [b[0] for b in BENCH]

def pct(b, v):
    if v is None: return None
    if b == "brief": return (v - 500) / 20.0
    if b == "omni": return max(0.0, float(v))
    return float(v)

combos = []
for mid, rows in ROWS.items():
    for lv, r in rows.items():
        combos.append((mid, lv, r))
best = {b: max(pct(b, r[b]) for _, _, r in combos if r.get(b) is not None) for b in BK}

def score(r, tw):
    return sum(w * pct(b, r[b]) / best[b] * 10 for b, w in tw.items())

cells = {}
for mid, lv, r in combos:
    cells.setdefault(mid, {})
    cells[mid][lv] = {"s": {t[0]: round(score(r, t[2]), 2) for t in TASKS}, "cost": r["cost"], "time": r["time"], "ii": r["ii"]}

def pool(group_filter):
    return [(mid, lv, c) for mid, d in cells.items() for lv, c in d.items() if group_filter(MD[mid][3])]

def picks(pl, tid):
    withcost = [x for x in pl if x[2]["cost"] is not None]
    top = max(x[2]["s"][tid] for x in pl)
    topc = max(pl, key=lambda x: x[2]["s"][tid])
    q = min([x for x in withcost if x[2]["s"][tid] >= .97 * top], key=lambda x: x[2]["cost"])
    v = min([x for x in withcost if x[2]["s"][tid] >= .90 * top], key=lambda x: x[2]["cost"])
    sp = min([x for x in pl if x[2]["s"][tid] >= .75 * top and x[2]["time"]], key=lambda x: x[2]["time"])
    return {"top": round(top, 2), "topCombo": topc[:2], "quality": q[:2], "value": v[:2], "speed": sp[:2]}

recs = {"claude": {}, "all": {}}
for tid, *_ in TASKS:
    recs["claude"][tid] = picks(pool(lambda g: g in ("claude", "claudeold")), tid)
    recs["all"][tid] = picks(pool(lambda g: True), tid)

# per-model effort ladders (models with >=3 measured levels)
ladders = {}
for mid, d in cells.items():
    lvs = [l for l in LV if l in d]
    if len(lvs) < 3: continue
    t = {}
    for tid, *_ in TASKS:
        s = [d[l]["s"][tid] for l in lvs]; mx = max(s)
        first = lambda th: lvs[next(i for i, v in enumerate(s) if v >= th * mx)]
        t[tid] = {"s": s, "max": mx, "argmax": lvs[s.index(mx)], "p97": first(.97), "p90": first(.90), "p75": first(.75)}
    ladders[mid] = {"levels": lvs, "tasks": t}

models = []
for m in META:
    mid = m[0]
    models.append({"id": mid, "label": m[1], "vendor": m[2], "group": m[3], "price": m[4], "open": m[5], "release": m[6],
                   "appDefault": m[7], "note": m[8], "levels": [l for l in LV if l in ROWS[mid]]})

out = {"asof": ASOF, "levels": LV, "benches": [dict(k=b[0], name=b[1], unit=b[2], why=b[3], w=b[4]) for b in BENCH],
       "tasks": [dict(id=t[0], name=t[1], weights=t[2]) for t in TASKS], "models": models, "rows": ROWS, "best": best,
       "cells": cells, "recs": recs, "ladders": ladders, "lbOnly": [[k[0], k[1], *v] for k, v in LB_ONLY.items()]}
json.dump(out, open("data6.json", "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    for tid, name, _ in TASKS:
        print(tid, name, "CLAUDE", recs["claude"][tid], "\n      ALL", recs["all"][tid])
    print()
    for mid in cells:
        print(f"{mid:9}", " ".join(f"{lv[:3]}:" + ",".join(f"{c['s'][t[0]]:.1f}" for t in TASKS) + f" ${c['cost']}" for lv, c in cells[mid].items()))
