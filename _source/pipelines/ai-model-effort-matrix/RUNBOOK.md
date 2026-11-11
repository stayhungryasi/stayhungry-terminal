# AI model × effort matrix — monthly refresh runbook

Pipeline for `/r/ai-model-effort-matrix/` on stayhungryasi.com. Lives in `_source/pipelines/ai-model-effort-matrix/`; the published page is `_source/research/ai-model-effort-matrix/app.html` + `meta.json`. Run all commands from this folder. Everything here is public; never add private wording to these files.

## Files
| File | Role |
|---|---|
| `aa_v6.py` | Artificial Analysis (AA) Intelligence Index v5.0.1 rows: Anthropic + Google + Meta + other labs, per effort level |
| `aa_v6_gpt.py` | OpenAI rows |
| `compute_v6.py` | Model list (META), task weights, scoring, recommendations → `data6.json` |
| `build6.py` | Text (findings, notes, sources) + `head6.html` + `body6.html` → page. `--hub` wraps for the hub iframe, `--out FILE` |
| `check6.py` | Pre-publish checks. Exit 1 = do not publish |
| `make_meta.py` | Hub meta.json (4 languages) from data6.json |
| `head6.html`, `body6.html` | Page styles and layout/JS |
| `data6_prev.json` | Last published data (for month-over-month comparison) |

## Monthly procedure
1. **Ruler check.** Open https://artificialanalysis.ai/methodology/intelligence-benchmarking. If the index version is no longer v5.0.x, or the benchmark list or weights changed: STOP, do not publish, and report what changed (the task mapping must be redesigned by a person).
2. **New models.** Check https://artificialanalysis.ai/leaderboards/models (top 40) and the vendors' news pages (Anthropic, OpenAI, Google, Meta, xAI, DeepSeek, Moonshot, Alibaba, Tencent, Mistral). Add any model that enters the AA top 40 or is a new flagship of a listed vendor; drop models AA no longer lists. New model = new META line in `compute_v6.py` (id, label, vendor, group, price, open weights, release date, app default, note).
3. **Fetch rows.** For every model in `aa_v6.py` / `aa_v6_gpt.py`, refetch AA comparison pages (`/models/comparisons/<a>-vs-<b>`, e.g. `claude-fable-5-2-low-vs-claude-fable-5-2-xhigh`, `...-medium-vs-...-high`, and a max pairing). Confirm each page says v5.0.x; AA serves stale cached pages — append `?nocache=<date>` when a page shows GDPval/SciCode/LCR (v4) columns. Record: ii, brief, auto, gdppdf, fc, tb4, tbsci, crit, omni, hled, cost, out, speed, e2e, time.
4. **Cross-check.** Fetch three combos a second time from a different comparison page (the current #1, the Claude value pick, the cheapest frontier point). Index and benchmark values must match exactly; cost within 3%, time within 10%.
5. **Compute + check.** `python3 compute_v6.py && python3 check6.py --prev data6_prev.json`. Any ERROR → STOP, report, do not publish. WARNINGs about index moves ≥6 must be explained in the findings.
6. **Text.** Most findings are computed from data, but `build6.py` also has hand-written sentences (EXTRA, effNotes, newRel, verdicts, support, uncert, sources). Re-read every one against the new data and sources; rewrite anything no longer true; add the month's new releases to `newRel` (keep the last ~10); mark reversed conclusions with an `["x","정정", ...]` finding.
7. **Build.** `python3 build6.py --hub --out ../../research/ai-model-effort-matrix/app.html`, then `python3 check6.py ../../research/ai-model-effort-matrix/app.html`.
8. **Hub metadata.** `python3 make_meta.py ../../research/ai-model-effort-matrix/meta.json` (regenerates date, asof, dek, key, 3 points in en/ko/es/ja from the data; edit the wording if this month's story differs). Every number in meta.json must appear in app.html — verify by script.
9. **Publish** with the stayhungry-hub-update procedure: changelog entry (4 languages, `"h":"HEAD"`), regenerate `_source/template.html`, build to a scratch dir, copy outputs (never crisis.json / fear.json), Playwright screenshots (1440×900, 1280×760, 390×860; ko/en/es/ja), forbidden-term scan, commit, `git fetch` + rebase, push, pin the changelog hash, verify live.
10. **Archive.** Copy the new `data6.json` to `data6_prev.json` in the same commit.
11. **Report** (Korean, to the site owner): what changed this month (new models, rank changes, recommendation changes), anything that stopped the run, and unverifiable items.

## Guardrails
- Never publish numbers that were not read from an AA page this run. If a model's page cannot be fetched, keep last month's row only if AA still lists the same values on its leaderboard; otherwise drop the model and say so.
- Scores are a weighted mapping of AA benchmarks (estimates); say so on the page.
- Credit line: stayhungryasi.com
