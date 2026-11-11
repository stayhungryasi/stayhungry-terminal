"""Assemble v6 dashboard: data6.json + text (X) + template (old CSS head + body6.html)."""
import json, re, sys
d = json.load(open("data6.json", encoding="utf-8"))
C, R, T = d["cells"], d["rows"], [t["id"] for t in d["tasks"]]
TN = {t["id"]: t["name"] for t in d["tasks"]}
LVK = {"low": "낮음", "medium": "중간", "high": "높음", "xhigh": "엑스트라", "max": "최대"}
LAB = {m["id"]: m["label"].replace("Claude ", "") for m in d["models"]}
def s(m, l, t): return C[m][l]["s"][t]
def cost(m, l): return C[m][l]["cost"]
def tm(m, l): return C[m][l]["time"]
def money(v): return f"${v:.2f}"
def mins(v): return f"{v/60:.1f}분" if v / 60 < 10 else f"{round(v/60)}분"
def nm(m, l): return f"{LAB[m]} {LVK[l]}"
def pct(a, b): return round(a / b * 100)
def wins(a, b):
    w = sum(1 for t in T if s(*a, t) - s(*b, t) >= 0.2); tie = sum(1 for t in T if abs(s(*a, t) - s(*b, t)) < 0.2)
    return w, tie, 5 - w - tie

# ---------------- hero: cheapest Claude combo that is >= current setting on every task
cur = ("fable51", "xhigh")
cands = [(m, l) for m in C for l in C[m] if d["models"][[x["id"] for x in d["models"]].index(m)]["group"] in ("claude", "claudeold")
         and all(s(m, l, t) >= s(*cur, t) for t in T) and cost(m, l) is not None]
to = min(cands, key=lambda x: cost(*x))
hero = {"from": list(cur), "to": list(to)}

f52 = R["fable52"]; o55 = R["opus55"]; f51 = R["fable51"]
bigShift = (f"<span><b>10/24 이후 바뀐 것 두 가지.</b> ① 11월 9일 출시된 <b>Claude Fable 5.2</b>가 AA 지수 {f52['max']['ii']}로 1위가 됐습니다. "
            f"토큰 단가는 $8/$40로 Fable 5.1보다 20% 낮고, 가장 낮은 단계({f52['low']['ii']}, 과제당 {money(f52['low']['cost'])})가 Opus 5.5 높음({o55['high']['ii']}, {money(o55['high']['cost'])})보다 높고 쌉니다. "
            f"10/24판의 결론(‘Opus 5.5가 전 영역 최고’)은 이제 틀렸습니다. ② Artificial Analysis가 10월 27일 지수를 v5로 바꿔 GDPval·SciCode·AA-LCR·HLE를 빼고 FrontierCode 2.0·Terminal-Bench-Science·HLE-Diamond를 넣었습니다. "
            f"그래서 점수 체계와 업무 매핑을 새로 짰고, 10/24판 숫자와는 직접 비교할 수 없습니다.</span>")

# ---------------- reasons per pick
def why(scope, tid, k):
    r = d["recs"][scope][tid]; m, l = r[k]; top = r["top"]; tc = r["topCombo"]
    base = f"최고점({nm(*tc)}, {top:.1f})의 {pct(s(m,l,tid), top)}%를 과제당 {money(cost(m,l))}로." if [m, l] != list(tc) else f"업무 점수 1위({top:.1f}). 과제당 {money(cost(m,l))}, {mins(tm(m,l))}."
    if k == "speed": base = f"최고점의 {pct(s(m,l,tid), top)}%를 과제당 {mins(tm(m,l))}에."
    return base
EXTRA = {
 "t1": {"quality": "Fable 5.2는 높음에서 FrontierCode 2.0 49.1%·Terminal-Bench 4.0 59.6%로 크게 뛰고, 그 위 단계는 비용만 늘어납니다.",
        "value": "가성비 기준(90%)에서도 같은 조합이 가장 쌉니다.",
        "allValue": "Gemini 4 Carbon 높음: Terminal-Bench 4.0 65.2%로 측정 모델 중 상위권. 다만 일반 공개 전(사이버 방어 기관·Fairwind 프로그램 먼저)이라 지금 바로 쓰기 어렵습니다."},
 "t2": {"quality": "환각 억제(AA-Omniscience) 67로 측정 모델 중 최고. 단 GDP.pdf(긴 전문 문서)는 24.2%로 Opus 5.5 높음(28.8%)·GPT-6 Astra(30–32%)보다 낮습니다.",
        "value": "앱 기본값(중간) 그대로. 환각 억제 64로 Opus 5.5 최대(48)보다 높습니다."},
 "t3": {"quality": "HLE-Diamond 80.2%, CritPt v2 76.5%로 리서치 지표는 최대까지 계속 오릅니다. 대신 과제당 44분.",
        "value": "중간→높음에서 HLE-Diamond 66.3→73.8%로 가장 크게 뜁니다."},
 "t4": {"quality": "직접 대응 벤치가 없어 근거가 가장 약한 업무입니다(FrontierCode 비중 45%).",
        "value": "Fable 5.2 중간은 최고점의 87%로 기준선 아래. 엑스트라 Opus가 Fable 5.2 높음보다 33% 쌉니다."},
 "t5": {"quality": "높음 이후로는 점수가 거의 안 오릅니다(높음 9.4 → 최대 9.5, 비용 ×2.9).",
        "value": "Fable 5.2 중간은 최고점의 89%로 기준선에 살짝 못 미칩니다.",
        "allValue": "GPT-6 Astra 엑스트라: Claude 가성비 조합보다 40% 쌉니다. ChatGPT 구독이 있으면 대안."},
}
reasons = {}
for tid in T:
    reasons[tid] = {k: why("claude", tid, k) + " " + EXTRA[tid].get(k, "") for k in ("quality", "value", "speed")}
    reasons[tid]["allValue"] = why("all", tid, "value") + " " + EXTRA[tid].get("allValue", "")

# ---------------- findings
cb = R["carbon"]["high"]; sol = R["sol61"]; ter = R["terra61"]; ast = R["astra"]; kimi = R["kimi"]["max"]; em = R["ember"]["max"]; hk = R["haiku55"]
w_sol = wins(("sol61", "max"), ("opus55", "medium"))
w_em = wins(("ember", "max"), ("haiku55", "max"))
findings = [
 ["v", "검증", f"Fable 5.2(11/9): 토큰 단가 $8/$40(Fable 5.1 $10/$50에서 20% 인하), 5단계 모두 지원, 앱·Claude Code 기본 중간·API 기본 높음. AA 지수 {f52['low']['ii']} → {f52['medium']['ii']} → {f52['high']['ii']} → {f52['xhigh']['ii']} → {f52['max']['ii']}, 과제당 {money(f52['low']['cost'])} → {money(f52['medium']['cost'])} → {money(f52['high']['cost'])} → {money(f52['xhigh']['cost'])} → {money(f52['max']['cost'])}."],
 ["v", "검증", f"같은 비용대 비교: Fable 5.2 낮음(지수 {f52['low']['ii']}, {money(f52['low']['cost'])})이 Opus 5.5 높음({o55['high']['ii']}, {money(o55['high']['cost'])})보다 높고 싸고, Fable 5.2 높음({f52['high']['ii']}, {money(f52['high']['cost'])})이 Opus 5.5 최대({o55['max']['ii']}, {money(o55['max']['cost'])})보다 높고 쌉니다. 단 벤치별로는 Opus 5.5 높음이 AA-Briefcase({o55['high']['brief']} vs {f52['low']['brief']})·Terminal-Bench 4.0({o55['high']['tb4']}% vs {f52['low']['tb4']}%)·GDP.pdf({o55['high']['gdppdf']}% vs {f52['low']['gdppdf']}%)에서 앞섭니다."],
 ["v", "검증", f"가장 큰 격차는 환각 억제(AA-Omniscience v1.1): Fable 5.2 {f52['low']['omni']}–{f52['max']['omni']} vs Opus 5.5 {o55['low']['omni']}–{o55['max']['omni']}, Gemini 4 Carbon 높음 {cb['omni']}, GPT-6 Astra {ast['low']['omni']}–{ast['high']['omni']}. 숫자를 다루는 기업분석·리서치에서 Fable 5.2가 앞서는 주된 이유입니다."],
 ["v", "검증", f"Fable 5.2의 약점: 긴 전문 문서(GDP.pdf)는 노력을 올릴수록 오히려 {f52['low']['gdppdf']}% → {f52['xhigh']['gdppdf']}%로 떨어지고(최대 {f52['max']['gdppdf']}%), 최고는 GPT-6 Astra 엑스트라 {ast['xhigh']['gdppdf']}%입니다. Terminal-Bench 4.0도 최대 {f52['max']['tb4']}%로 Opus 5.5 최대와 같고, Kimi K3.1 Pro {kimi['tb4']}%·Gemini 4 Carbon {cb['tb4']}%보다 낮습니다."],
 ["v", "검증", f"Fable 5.2 높음 이상은 토큰을 많이 써서 과제당 비용이 Fable 5.1보다 비쌉니다(높음 {money(f52['high']['cost'])} vs {money(f51['high']['cost'])}, 최대 {money(f52['max']['cost'])} vs {money(f51['max']['cost'])}). 낮음·중간은 더 쌉니다({money(f52['low']['cost'])} vs {money(f51['low']['cost'])}, {money(f52['medium']['cost'])} vs {money(f51['medium']['cost'])})."],
 ["v", "검증", f"Google Gemini 4 Carbon(10/28): Anthropic 밖 1위, 높음 지수 {cb['ii']}·과제당 {money(cb['cost'])}. AutomationBench {cb['auto']}%로 Fable 5.2 최대({f52['max']['auto']}%)보다 높습니다. 다만 일반 공개 전이라 사이버 방어 기관·Fairwind 프로그램부터 열립니다."],
 ["v", "검증", f"OpenAI 가성비: GPT-6.1 Sol 최대(지수 {sol['max']['ii']}, {money(sol['max']['cost'])})가 Opus 5.5 중간({o55['medium']['ii']}, {money(o55['medium']['cost'])})보다 5개 업무 중 {w_sol[0]}개에서 높고 비용은 절반입니다. 새 GPT-6.1 Terra(10/26, $1/$5)는 최대 {ter['max']['ii']}·{money(ter['max']['cost'])}. 둘 다 ChatGPT에선 Work·Codex에서만 쓸 수 있고 일반 채팅엔 없습니다."],
 ["v", "검증", f"경량급: Meta Muse Ember(11/9, $0.10/$0.50)가 지수 {em['ii']}·과제당 {money(em['cost'])}로 Claude Haiku 5.5 최대({hk['max']['ii']}, {money(hk['max']['cost'])})와 지수가 같고 비용은 3분의 1입니다. 업무 점수는 {w_em[0]}개 우위·{w_em[1]}개 동급·{w_em[2]}개 열위."],
 ["v", "검증", f"오픈 웨이트 1위는 Kimi K3.1 Pro(지수 {kimi['ii']}, {money(kimi['cost'])}, Terminal-Bench 4.0 {kimi['tb4']}%). 다만 과제당 {mins(kimi['time'])}로 가장 느린 축입니다."],
 ["v", "검증", f"Sonnet 5.5는 곡선이 가장 가파릅니다: 지수 {R['sonnet55']['low']['ii']} → {R['sonnet55']['medium']['ii']} → {R['sonnet55']['high']['ii']} → {R['sonnet55']['xhigh']['ii']} → {R['sonnet55']['max']['ii']}. 최대는 과제당 {money(R['sonnet55']['max']['cost'])}로 Opus 5.5 최대({money(o55['max']['cost'])})와 비슷한데 점수는 낮습니다."],
 ["x", "정정", f"10/24판의 ‘Fable 5.1 엑스트라 → Opus 5.5 높음이면 비용 30%’는 옛 지수(v4.3) 기준입니다. v5 기준으로는 {money(o55['high']['cost'])} vs {money(f51['xhigh']['cost'])}로 {pct(o55['high']['cost'], f51['xhigh']['cost'])}%이고, 지금은 Fable 5.2 낮음이 더 싸고({pct(f52['low']['cost'], f51['xhigh']['cost'])}%) 5개 업무 모두 더 높습니다."],
 ["x", "정정", f"AA 지수 v5로 같은 모델의 점수도 바뀌었습니다(예: Fable 5.1 최대 53 → {f51['max']['ii']}, Haiku 5.5 최대 43 → {hk['max']['ii']}, Opus 5.5 최대 58 → {o55['max']['ii']}). 과제 구성이 바뀌어 과제당 비용도 대체로 두 배 가까이 올랐습니다(Opus 5.5 최대 $5.98 → {money(o55['max']['cost'])}). 모델이 나빠진 게 아니라 잣대가 바뀐 것입니다."],
]
uncert = [
 ["Fable 5.2 우위의 상당 부분은 환각 억제 점수입니다", "AA-Omniscience를 빼고 다시 계산하면 기업분석·리서치에서 Fable 5.2 낮음은 Fable 5.1 엑스트라와 동급이 되고, 기업분석은 Opus 5.5 높음이 앞섭니다. 코딩 3개 업무의 우위는 그대로입니다. ‘모르면 모른다고 하는 성향’이 실제 업무에서 얼마나 중요한지가 결론을 좌우합니다.", "실측 #2·#3·#7·#8·#16"],
 ["구독 사용량은 API 비용과 다릅니다", "Anthropic은 출시 프로모션으로 Fable을 Pro·Team 표준 좌석 주간 한도의 최대 50%까지 쓸 수 있게 했다고 밝혔습니다. 과제당 비용이 싸도 앱에서 Fable 5.2를 쓰면 한도가 더 빨리 찰 수 있고, 앱 메뉴에 Fable 5.2가 언제 보이는지도 확인하지 못했습니다.", "실측 #1–10 (사용량 체감 칸)"],
 ["업무 매핑은 제 판단입니다", "AA v5의 9개 벤치를 5대 업무에 가중합했습니다. 게임 개발은 직접 대응 벤치가 없어 가장 약하고, 한국어·국내 종목 맥락은 어느 벤치도 재지 않습니다.", "실측 #2·#3·#7·#8·#11·#12"],
 ["독립 평가 교차 확인을 못 했습니다", "이번엔 Vals AI 페이지에 접근하지 못해 최신 Vals 순위를 반영하지 않았습니다. 10/24엔 Vals 1위가 Sonnet 5.5였고, Fable 5.2는 Vals 결과를 아직 보지 못했습니다.", "실측 #16·#18"],
]
# ---------------- crossover pairs
PAIRS_RAW = [
 (("fable52", "low"), ("fable51", "xhigh"), "현재 설정을 대체할 수 있나"),
 (("fable52", "medium"), ("opus55", "high"), "앱 기본값 vs Opus 권장 기본"),
 (("fable52", "high"), ("opus55", "max"), "Fable 5.2 높음이 Opus 최대를 대체하나"),
 (("opus55", "xhigh"), ("fable52", "medium"), "Opus를 올릴까, Fable을 기본으로 쓸까"),
 (("sonnet55", "xhigh"), ("opus55", "high"), "Sonnet 엑스트라 vs Opus 높음"),
 (("carbon", "high"), ("fable52", "high"), "구글 최상위 vs Fable 5.2 높음"),
 (("astra", "xhigh"), ("opus55", "high"), "GPT 최상위 vs Opus 권장 기본"),
 (("sol61", "max"), ("opus55", "medium"), "GPT 가성비 vs Opus 기본값"),
 (("sol61", "max"), ("fable52", "low"), "GPT 가성비 vs Fable 5.2 최저"),
 (("terra61", "max"), ("sol61", "max"), "새 Terra vs 6.1 Sol"),
 (("kimi", "max"), ("opus55", "medium"), "오픈 웨이트 1위 vs Opus 기본값"),
 (("ember", "max"), ("haiku55", "max"), "경량급: Meta vs Anthropic"),
]
pairs = []
for a, b, q in PAIRS_RAW:
    if a[0] not in C or b[0] not in C: continue
    w, tie, l = wins(a, b); r = cost(*a) / cost(*b)
    if l == 0 and w >= 1: v = f"왼쪽이 같거나 높음({w}개 우위·{tie}개 동급), 비용 {r:.2f}배" + (" → 대체 가능" if r <= 1.1 else " → 비싸지만 더 좋음")
    elif w == 0 and l >= 1: v = f"오른쪽이 같거나 높음({l}개 우위·{tie}개 동급), 비용 비 {r:.2f}" + (" → 왼쪽이 싸면 절약용" if r < 0.9 else " → 오른쪽 유지")
    elif w == 0 and l == 0: v = f"5개 업무 모두 동급, 비용 {r:.2f}배"
    else: v = f"{w}개 우위·{tie}개 동급·{l}개 열위, 비용 {r:.2f}배 → 업무별로 갈림"
    pairs.append([list(a), list(b), q, v])

# ---------------- effort notes
def gain(m, a, b): return R[m][b]["ii"] - R[m][a]["ii"]
effNotes = {
 "fable52": f"지수가 가장 크게 뛰는 구간은 중간→높음(+{gain('fable52','medium','high')}, 비용 ×{f52['high']['cost']/f52['medium']['cost']:.1f})이고, 엑스트라는 높음과 지수가 같습니다.",
 "opus55": f"엑스트라에서 지수 +{gain('opus55','high','xhigh')}(비용 ×{o55['xhigh']['cost']/o55['high']['cost']:.1f}). Terminal-Bench 4.0은 엑스트라부터 {o55['xhigh']['tb4']}%로 멈춥니다.",
 "sonnet55": "낮음·중간은 다른 모델의 낮음보다도 약해, Sonnet은 엑스트라 이상에서만 쓸 만합니다.",
 "fable51": f"최대(지수 {f51['max']['ii']})가 엑스트라({f51['xhigh']['ii']})보다 낮은 과잉사고 구간이 있습니다. CritPt v2는 {f51['xhigh']['crit']}% → {f51['max']['crit']}%로 떨어집니다.",
 "haiku55": "최대에서도 Terminal-Bench 4.0 32.8%라 코딩 에이전트 주력으로는 부족합니다.",
 "astra": f"최대는 엑스트라보다 비용 ×{ast['max']['cost']/ast['xhigh']['cost']:.1f}에 지수 +{gain('astra','xhigh','max')}뿐입니다.",
 "sol61": f"최대(과제당 {money(sol['max']['cost'])})까지 올려도 Claude Opus 5.5 중간({money(o55['medium']['cost'])})보다 쌉니다.",
 "terra61": f"최대에서 지수가 {ter['xhigh']['ii']} → {ter['max']['ii']}로 크게 뛰지만 비용도 ×{ter['max']['cost']/ter['xhigh']['cost']:.1f}입니다.",
}
newRel = [
 ["2026-11-09", "Claude Fable 5.2 · Mythos 5.2", f"$8/$40, AA 지수 1위({f52['max']['ii']}). Mythos 5.2는 검증된 기관만, AA 미측정", "https://www.anthropic.com/claude-fable-and-mythos-5-2"],
 ["2026-11-09", "Meta Muse Ember", f"$0.10/$0.50, AA {em['ii']} · 과제당 {money(em['cost'])}", "https://techcrunch.com/2026/11/09/meta-releases-muse-ember-a-new-lightweight-model-for-agent-execution/"],
 ["2026-11-05", "Inkling 2 Small (Thinking Machines)", f"594B/17B 활성, AA {R['inkling']['max']['ii']}, 웨이트 공개 예정", ""],
 ["2026-11-05", "GPT-6-Cyber", "보안 전용, 승인제($20/$100). AA 미측정", "https://deploymentsafety.openai.com/gpt-6-cyber"],
 ["2026-11-03", "Tencent Hy4", f"770B/49B 활성, AA {R['hy4']['max']['ii']}, 웨이트 공개 예정", "https://www.tencent.com/tencent-launches-hy4-joining-the-ranks-of-the-worlds-leading-open-source-ai-models/"],
 ["2026-10-30", "GPT-6 Rosalind", "생명과학 전용, 승인제($15/$75). AA 미측정", ""],
 ["2026-10-29", "Mistral Large 4 (오픈 웨이트)", f"$0.70/$2.10, AA {R['mistral']['high']['ii']}", "https://mistral.ai/news/mistral-large-4-oss/"],
 ["2026-10-29", "GPT-6 Luna 동작 업데이트", "ChatGPT 무료 기본 모델, 답변 간결화(사실 오류율은 OpenAI 부록상 상승)", "https://deploymentsafety.openai.com/gpt-6-luna-october-28-2026-addendum"],
 ["2026-10-28", "Google Gemini 4 Carbon", f"AA {cb['ii']}(높음), 출시가 $2/$10 → 이후 $4/$20, 제한 공개", "https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon/"],
 ["2026-10-27", "AA Intelligence Index v5", "벤치 구성 변경(현재 v5.0.1). 이 대시보드 전면 재계산의 이유", "https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v5"],
 ["2026-10-26", "GPT-6.1 Terra", f"$1/$0.05/$5, AA 최대 {ter['max']['ii']} · {money(ter['max']['cost'])}, ChatGPT는 Work·Codex만", "https://developers.openai.com/api/docs/models/gpt-6.1-terra"],
]
verdicts = [
 ["Claude Fable 5.1", "없음", f"Fable 5.2가 같은 단계 5개 전부에서 AA 지수가 높고({', '.join(f'{LVK[l]} {f51[l][chr(105)+chr(105)]}→{f52[l][chr(105)+chr(105)]}' for l in ['low','medium','high','xhigh','max'])}), 토큰 단가도 20% 낮음."],
 ["Claude Opus 5", "없음", f"v5 기준 최대 지수 {R['opus5']['max']['ii']} vs Opus 5.5 최대 {o55['max']['ii']}, 과제당 {money(R['opus5']['max']['cost'])} vs {money(o55['max']['cost'])}."],
 ["Claude Fable 5", "없음", "v5 지수 미측정(AA가 Opus 4.8로 대체 실행). 옛 지수(v4.3) 50으로 Fable 5.1보다 낮았음."],
 ["Claude Opus 4.8 · 4.7 · 4.6 · Opus 3", "없음", "v5 지수 미측정. 옛 지수 기준 42 · 41(추정) · 32(추정) · 9(추정)."],
 ["Claude Sonnet 5 · Sonnet 4.6", "없음", "v5 지수 미측정. 옛 지수 38 · 30으로 Sonnet 5.5(옛 지수 56)에 크게 뒤짐."],
 ["Claude Haiku 4.5", "없음", "Haiku 5.5가 토큰 단가 90% 저렴($0.10/$0.50, 10만 토큰 이하). Anthropic 문서상 퇴역 예정일(10/15 이후)은 지났지만 아직 사용 가능으로 표시."],
]
support = [
 ["Fable 5.2", ["low","medium","high","xhigh","max"], "높음", "중간", "$8 / $40"],
 ["Opus 5.5", ["low","medium","high","xhigh","max"], "중간", "미확인", "$4 / $20"],
 ["Sonnet 5.5", ["low","medium","high","xhigh","max"], "높음", "중간", "$2 / $10"],
 ["Haiku 5.5", ["low","medium","high","xhigh","max"], "중간", "미확인", "$0.10 / $0.50"],
 ["Fable 5.1", ["low","medium","high","xhigh","max"], "높음", "중간", "$10 / $50"],
 ["Opus 4.6 · Sonnet 4.6", ["low","medium","high","max"], "높음", "—", "$5/$25 · $3/$15"],
 ["Haiku 4.5", [], "노력 미지원", "—", "$1 / $5"],
]
supportNote = "API 기본값은 Anthropic 노력 문서(11/11), 앱 기본값은 각 모델 발표문 기준. Fable은 출시 프로모션으로 Pro·Team 표준 좌석 주간 사용 한도의 최대 50%까지 쓸 수 있습니다(Anthropic 발표). 단계명은 영문 도움말 ‘Extra high (xhigh)’, 한국어 도움말 ‘매우 높음(xhigh)’, 앱 화면은 ‘엑스트라’입니다."
formula = [
 "벤치 원점수를 백분율로 통일: AA-Briefcase Elo는 (Elo − 500) ÷ 20, AA-Omniscience 음수는 0.",
 "벤치마다 측정된 모든 모델·노력 조합 중 최고값을 10으로 정규화.",
 "업무 점수 = 정규화 점수의 업무별 가중합(가중치는 위 표).",
 "모든 점수는 AA Intelligence Index v5.0.1이 그 모델·노력 조합을 직접 잰 값에서만 나옵니다. 다른 모델 곡선을 빌리거나 보간한 값은 없습니다(10/24판과 다른 점).",
 "추천: 최고품질 = 최고점의 97% 이상 중 과제당 비용 최소, 가성비 = 90% 이상 중 비용 최소, 속도 = 75% 이상 중 과제당 시간 최소. ‘Claude’ 추천은 Claude 모델만, ‘전 벤더’는 전부를 후보로 씁니다.",
 "과제당 비용·시간은 AA가 지수 전체 과제를 돌릴 때의 평균입니다. 구독 앱의 사용량 소모와 비례한다는 보장은 없습니다.",
 "Gemini 4 Carbon 중간(지수 58, 과제당 $6.59)은 벤치별 값을 확보하지 못해 업무 점수에서 뺐습니다.",
]
v5note = ("<span><b>왜 10/24판과 숫자가 다른가.</b> Artificial Analysis가 10월 27일 지수를 v5로 바꿨습니다(현재 v5.0.1). "
          "빠진 벤치: GDPval-AA·SciCode·AA-LCR·HLE. 새로 들어온 벤치: FrontierCode 2.0·Terminal-Bench-Science 0.1·HLE-Diamond. 바뀐 벤치: CritPt → CritPt v2(Hard), AA-Omniscience → v1.1. "
          "과제 구성이 달라 같은 모델도 지수와 과제당 비용이 바뀌었습니다. 이 대시보드는 v5 벤치만으로 업무 매핑을 새로 짰습니다. "
          "또 v5에선 CursorBench·FrontierCode 1.1 같은 공급사 자체 측정값을 쓰지 않습니다. FrontierCode 2.0을 AA가 직접 재기 때문입니다.</span>")
sources = [
 ["Anthropic", "Claude Fable 5.2 and Mythos 5.2 (2026-11-09)", "https://www.anthropic.com/claude-fable-and-mythos-5-2"],
 ["Claude Platform Docs", "Pricing — Fable 5.2 $8/$40", "https://platform.claude.com/docs/en/about-claude/pricing"],
 ["Claude Platform Docs", "Effort — 단계·기본값", "https://platform.claude.com/docs/en/build-with-claude/effort"],
 ["Claude Platform Docs", "Models overview", "https://platform.claude.com/docs/en/about-claude/models/overview"],
 ["Claude Platform Docs", "Model deprecations", "https://platform.claude.com/docs/en/about-claude/model-deprecations"],
 ["Artificial Analysis", "Intelligence Index v5 발표 (2026-10-27)", "https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v5"],
 ["Artificial Analysis", "방법론 — v5.0.1 벤치·가중치", "https://artificialanalysis.ai/methodology/intelligence-benchmarking"],
 ["Artificial Analysis", "모델 순위표", "https://artificialanalysis.ai/leaderboards/models"],
 ["Artificial Analysis", "Fable 5.2 vs Opus 5.5 (최대)", "https://artificialanalysis.ai/models/comparisons/claude-fable-5-2-vs-claude-opus-5-5"],
 ["Artificial Analysis", "Opus 5.5 · Sonnet 5.5 · Fable 5.1 · Haiku 5.5 노력별 비교 페이지", "https://artificialanalysis.ai/models/comparisons/claude-opus-5-5-low-vs-claude-opus-5-5-xhigh"],
 ["Artificial Analysis", "GPT-6 Astra vs GPT-6.1 Sol 노력별 비교 페이지", "https://artificialanalysis.ai/models/comparisons/gpt-6-astra-high-vs-gpt-6-1-sol-high"],
 ["Artificial Analysis", "Gemini 4 Carbon vs Argon", "https://artificialanalysis.ai/models/comparisons/gemini-4-carbon-vs-gemini-4-argon"],
 ["Artificial Analysis", "Muse Wonder Full vs Kimi K3.1 Pro", "https://artificialanalysis.ai/models/comparisons/muse-wonder-full-vs-kimi-k3-1-pro"],
 ["OpenAI Developers", "GPT-6.1 Terra 모델 문서", "https://developers.openai.com/api/docs/models/gpt-6.1-terra"],
 ["OpenAI Developers", "API Pricing", "https://developers.openai.com/api/docs/pricing"],
 ["OpenAI", "GPT-6.1 Terra 시스템 카드 부록", "https://deploymentsafety.openai.com/gpt-6-1-terra"],
 ["Google", "Introducing Gemini 4 Carbon", "https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon/"],
 ["TechCrunch", "Meta releases Muse Ember", "https://techcrunch.com/2026/11/09/meta-releases-muse-ember-a-new-lightweight-model-for-agent-execution/"],
 ["Tencent", "Tencent launches Hy4", "https://www.tencent.com/tencent-launches-hy4-joining-the-ranks-of-the-worlds-leading-open-source-ai-models/"],
 ["Mistral", "Mistral Large 4 open weights", "https://mistral.ai/news/mistral-large-4-oss/"],
 ["Opper", "모델 출시 일지 (출시일 교차 확인)", "https://opper.ai/model-releases"],
]
prompts = {
 "t1": "첨부한 [파일명].py는 종목 스캐너 모듈이다.\n룰북의 다음 규칙 1개를 새 함수로 반영하라: [규칙 원문].\n\n조건\n- 기존 함수의 시그니처·반환형·기존 규칙 로직은 한 줄도 바꾸지 말 것\n- pytest 단위테스트 5개(정상 2, 경계 2, 예외 1)를 함께 작성\n- 변경 diff와 테스트 실행 결과만 제시",
 "t2": "첨부한 [종목] 재무데이터(최근 8분기)로 기업분석을 작성하라.\n1) 밸류에이션: PER·PBR·EV/EBITDA, 동종 3사 비교\n2) 표면 내러티브 → 숨은 의도 → 게임이론 프레이밍\n3) 가장 강력한 반론을 포함한 Bull 케이스\n4) 한 줄 결론\n\n모든 수치는 첨부 데이터에서만 인용하고 출처 행을 표시하라.",
 "t3": "웹검색으로 '2027년 HBM 공급과잉 리스크'를 리서치하라.\n- 최근 6개월 이내 1차 출처 위주\n- 모든 주장에 원문 링크\n- 반대 시나리오 포함\n- 결론은 3줄",
 "t4": "단일 HTML 파일로 우주선 슈팅 게임을 만들어라.\n- 방향키 이동, 스페이스 발사\n- 적 3종, 충돌판정\n- 점수·레벨업, 게임오버와 재시작\n- requestAnimationFrame 게임 루프\n- 외부 라이브러리 금지",
 "t5": "첨부 CSV(종목·등락률·거래대금)를 읽어 상위 20종목 표와 막대차트를 담은 A4 PDF를 WeasyPrint로 만들고, 텔레그램 봇 API로 지정 채팅에 전송하는 Python 스크립트를 작성하라.\n- 설정은 .env\n- 실패 시 재시도 3회와 로그\n- 실행 방법을 README로",
}
rubric = {
 "t1": [{"k":"run","l":"실행 성공","type":"toggle"},{"k":"keep","l":"기존 규칙·시그니처 보존","type":"slider"},{"k":"edge","l":"엣지케이스 처리","type":"slider"},{"k":"tests","l":"테스트 통과 수 (0–5)","type":"count5"}],
 "t2": [{"k":"errs","l":"수치 오류 개수 (직접 셈)","type":"errors"},{"k":"depth","l":"논리 깊이 (숨은 의도·게임이론)","type":"slider"},{"k":"counter","l":"반론의 강도","type":"slider"},{"k":"closer","l":"한 줄 클로저","type":"slider"}],
 "t3": [{"k":"cite","l":"원문이 확인되는 인용 비율 (%)","type":"pct"},{"k":"fresh","l":"소스 신선도","type":"slider"},{"k":"insight","l":"통찰","type":"slider"}],
 "t4": [{"k":"run","l":"첫 실행 작동","type":"toggle"},{"k":"bugs","l":"버그 수","type":"errors"},{"k":"feel","l":"조작감","type":"slider"},{"k":"visual","l":"비주얼","type":"slider"}],
 "t5": [{"k":"run","l":"첫 실행 성공","type":"toggle"},{"k":"req","l":"요구사항 충족률 (%)","type":"pct"},{"k":"loops","l":"디버깅 왕복 횟수","type":"errors"}],
}
plan = ([["fable51", "xhigh", t, "기준선: Fable 5.1 엑스트라"] for t in T] +
        [["fable52", "low", t, f"대체 후보 (비용 {pct(f52['low']['cost'], f51['xhigh']['cost'])}%)"] for t in T] +
        [["fable52", "medium", "t2", "앱 기본값으로 분석이 충분한가"], ["fable52", "medium", "t3", "앱 기본값으로 리서치가 충분한가"],
         ["fable52", "high", "t1", "고도화 최종본"], ["fable52", "high", "t4", "게임 최종본"],
         ["opus55", "xhigh", "t5", "Opus 엑스트라가 Fable 5.2를 대신하나"], ["opus55", "high", "t2", "Opus 권장 기본 vs Fable 5.2"],
         ["sonnet55", "xhigh", "t5", "Sonnet 엑스트라로 스크립트 충분한가"], ["sol61", "max", "t2", "GPT 가성비 교차 확인 (API·Codex)"],
         ["haiku55", "max", "t5", "바닥선: 최저가 Claude"], ["fable52", "max", "t3", "최대까지 올릴 가치"]])
planLede = "1–10번이 가장 중요합니다. Fable 5.1 엑스트라 설정을 Fable 5.2 낮음이 대체할 수 있는지 5개 업무 전부에서 확인하고, 사용량 체감 칸으로 구독 한도 소모도 함께 기록합니다."
genNote = "같은 노력 단계의 AA 실측끼리 비교. 단계 버튼으로 바꿔 보세요."
X = dict(hero=hero, bigShift=bigShift, reasons=reasons, findings=findings, uncert=uncert, pairs=pairs, effNotes=effNotes,
         newRel=newRel, newIds=["fable52", "ember", "inkling", "hy4", "mistral", "carbon", "terra61"], verdicts=verdicts, support=support,
         supportNote=supportNote, formula=formula, v5note=v5note, sources=sources, prompts=prompts, rubric=rubric, plan=plan,
         planLede=planLede, genNote=genNote, subline=f"실무 5대 업무 기준 · 현존 주요 모델 {len(d['models'])}종 × 노력 단계 = 조합 {sum(len(v) for v in C.values())}개 · 한 잣대(AA 지수 v5.0.1)",
         credit="stayhungryasi.com · 정보 제공 목적.")

head = open("head6.html", encoding="utf-8").read()
body = open("body6.html", encoding="utf-8").read()
page = head + "\n" + body
page = page.replace("/*__DATA__*/null", json.dumps(d, ensure_ascii=False, separators=(",", ":")), 1)
page = page.replace("/*__TEXT__*/null", json.dumps(X, ensure_ascii=False, separators=(",", ":")), 1)
# --overlay FILE : apply [[public, private], ...] replacements (private artifact build; overlay file is NOT in the public repo)
# --hub         : wrap as a full document for the hub iframe (noindex)
args = sys.argv[1:]
out = "model-effort-matrix.html"
if "--out" in args: out = args[args.index("--out") + 1]
if "--overlay" in args:
    for pub_s, priv_s in json.load(open(args[args.index("--overlay") + 1], encoding="utf-8")):
        page = page.replace(json.dumps(pub_s, ensure_ascii=False)[1:-1], json.dumps(priv_s, ensure_ascii=False)[1:-1]).replace(pub_s, priv_s)
if "--hub" in args:
    page = '<!doctype html><html><head><meta name="robots" content="noindex"><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>\n' + page + "\n</body></html>\n"
open(out, "w", encoding="utf-8").write(page)
print("built", len(page), "hero", hero)
