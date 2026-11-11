"""Write the hub meta.json (4 languages) from data6.json. Every number comes from the data.
usage: python3 make_meta.py <out meta.json>"""
import json, sys
d = json.load(open("data6.json", encoding="utf-8"))
R, C = d["rows"], d["cells"]
T = [t["id"] for t in d["tasks"]]
LAB = {m["id"]: m["label"] for m in d["models"]}
LVK = {"ko": {"low": "낮음", "medium": "중간", "high": "높음", "xhigh": "엑스트라", "max": "최대"},
       "en": {"low": "low", "medium": "medium", "high": "high", "xhigh": "extra high", "max": "max"},
       "es": {"low": "bajo", "medium": "medio", "high": "alto", "xhigh": "extra alto", "max": "máximo"},
       "ja": {"low": "低", "medium": "中", "high": "高", "xhigh": "エクストラ", "max": "最大"}}
nmodels = len(d["models"]); ncombos = sum(len(v) for v in C.values())
# leader by AA index
top_mid, top_lv = max(((m, l) for m in R for l in R[m]), key=lambda x: R[x[0]][x[1]]["ii"])
top_ii = R[top_mid][top_lv]["ii"]
# cheapest Claude combo that beats the reference setting on every task
ref = ("fable51", "xhigh")
grp = {m["id"]: m["group"] for m in d["models"]}
cands = [(m, l) for m in C for l in C[m] if grp[m] in ("claude", "claudeold") and C[m][l]["cost"] is not None
         and all(C[m][l]["s"][t] >= C[ref[0]][ref[1]]["s"][t] for t in T)]
to = min(cands, key=lambda x: C[x[0]][x[1]]["cost"])
pct = round(C[to[0]][to[1]]["cost"] / C[ref[0]][ref[1]]["cost"] * 100)
c_to, c_ref = C[to[0]][to[1]]["cost"], C[ref[0]][ref[1]]["cost"]
# best non-Anthropic
vend = {m["id"]: m["vendor"] for m in d["models"]}
na_mid, na_lv = max(((m, l) for m in R for l in R[m] if vend[m] != "Anthropic"), key=lambda x: R[x[0]][x[1]]["ii"])
na_ii, na_c = R[na_mid][na_lv]["ii"], R[na_mid][na_lv]["cost"]
# cheapest combo with index >= 55
cheap = min(((m, l) for m in R for l in R[m] if R[m][l]["ii"] >= 55 and R[m][l]["cost"] is not None), key=lambda x: R[x[0]][x[1]]["cost"])
ch_ii, ch_c = R[cheap[0]][cheap[1]]["ii"], R[cheap[0]][cheap[1]]["cost"]
def n(m, l, lang): return f"{LAB[m].replace('Claude ', '')} {LVK[lang][l]}" if lang != "en" else f"{LAB[m].replace('Claude ', '')} at {LVK[lang][l]}"
def money(v): return f"${v:.2f}"
meta = {
 "slug": "ai-model-effort-matrix", "date": d["asof"], "asof": f"{d['asof']} (Artificial Analysis v5.0.1)", "category": "ai",
 "title": {"ko": "AI 모델 × 노력 매트릭스", "en": "AI Models × Effort Matrix", "es": "Matriz de modelos de IA × esfuerzo", "ja": "AIモデル × 思考量マトリクス"},
 "dek": {
  "ko": f"Artificial Analysis 지수 v5.0.1 한 잣대로 {nmodels}개 모델의 노력 단계별 조합 {ncombos}개를 5대 업무에 매핑했다. 1위는 {n(top_mid, top_lv, 'ko')}(지수 {top_ii}). 매월 갱신한다.",
  "en": f"{nmodels} models and {ncombos} model-and-effort combinations mapped to five work tasks on one yardstick, the Artificial Analysis index v5.0.1. The leader is {n(top_mid, top_lv, 'en')} (index {top_ii}). Updated monthly.",
  "es": f"{nmodels} modelos y {ncombos} combinaciones de modelo y esfuerzo, aplicadas a cinco tareas con una sola vara: el índice v5.0.1 de Artificial Analysis. Lidera {n(top_mid, top_lv, 'es')} (índice {top_ii}). Se actualiza cada mes.",
  "ja": f"Artificial Analysis指数v5.0.1という一つの物差しで、{nmodels}モデル・思考量別{ncombos}通りの組み合わせを5つの業務に当てはめた。首位は{n(top_mid, top_lv, 'ja')}（指数{top_ii}）。毎月更新。"},
 "key": {"value": f"{pct}%", "label": {
  "ko": f"Fable 5.1 엑스트라 → {n(to[0], to[1], 'ko')}로 바꿀 때의 과제당 비용 (AA {money(c_to)} vs {money(c_ref)}, 5개 업무 모두 점수 상승)",
  "en": f"Cost per task when switching Fable 5.1 at extra high to {n(to[0], to[1], 'en')} (AA {money(c_to)} vs {money(c_ref)}; higher on all 5 tasks)",
  "es": f"Costo por tarea al pasar de Fable 5.1 extra alto a {n(to[0], to[1], 'es')} (AA {money(c_to)} vs {money(c_ref)}; mejor en las 5 tareas)",
  "ja": f"Fable 5.1「エクストラ」から{n(to[0], to[1], 'ja')}に替えたときのタスク当たりコスト（AA {money(c_to)} vs {money(c_ref)}、5業務すべてで上昇）"}},
 "points": {
  "ko": [f"Anthropic 밖 최고는 {LAB[na_mid]} {LVK['ko'][na_lv]}(지수 {na_ii}, 과제당 {money(na_c)}).",
         f"지수 55 이상을 가장 싸게 내는 조합은 {LAB[cheap[0]].replace('Claude ', '')} {LVK['ko'][cheap[1]]}(지수 {ch_ii}, 과제당 {money(ch_c)}).",
         "업무 점수는 AA 벤치를 5대 업무(시스템 고도화·기업분석·리서치·게임·프로그램 개발)에 가중합한 작성자 추정이다."],
  "en": [f"The best model outside Anthropic is {LAB[na_mid]} at {LVK['en'][na_lv]} (index {na_ii}, {money(na_c)} per task).",
         f"The cheapest way to an index of 55 or more is {LAB[cheap[0]].replace('Claude ', '')} at {LVK['en'][cheap[1]]} (index {ch_ii}, {money(ch_c)} per task).",
         "Task scores are the author's estimate: a weighted mix of AA benchmarks for systems work, company analysis, research, game and program development."],
  "es": [f"El mejor modelo fuera de Anthropic es {LAB[na_mid]} en {LVK['es'][na_lv]} (índice {na_ii}, {money(na_c)} por tarea).",
         f"La forma más barata de llegar a un índice de 55 o más es {LAB[cheap[0]].replace('Claude ', '')} en {LVK['es'][cheap[1]]} (índice {ch_ii}, {money(ch_c)} por tarea).",
         "Las puntuaciones por tarea son una estimación del autor: una mezcla ponderada de pruebas de AA para sistemas, análisis de empresas, investigación, juegos y programas."],
  "ja": [f"Anthropic以外の最上位は{LAB[na_mid]}「{LVK['ja'][na_lv]}」（指数{na_ii}、タスク当たり{money(na_c)}）。",
         f"指数55以上を最も安く出すのは{LAB[cheap[0]].replace('Claude ', '')}「{LVK['ja'][cheap[1]]}」（指数{ch_ii}、タスク当たり{money(ch_c)}）。",
         "業務スコアはAAのベンチマークを5業務（システム高度化・企業分析・リサーチ・ゲーム・プログラム開発）に加重した筆者の推定。"]},
 "tickers": [], "checkpoints": [],
 "tags": {"ko": ["AI 모델", "노력 설정", "월간 갱신", "벤치마크"], "en": ["AI models", "Effort settings", "Monthly", "Benchmarks"],
          "es": ["Modelos de IA", "Niveles de esfuerzo", "Mensual", "Benchmarks"], "ja": ["AIモデル", "思考量設定", "月次更新", "ベンチマーク"]},
}
json.dump(meta, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps({k: meta[k] for k in ("dek", "key")}, ensure_ascii=False)[:600])
