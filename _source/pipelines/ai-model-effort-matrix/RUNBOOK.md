# AI model × effort matrix — monthly refresh runbook

Pipeline for the hub's **AI models** page: reader page id `models` in the BUILT (만든 것) menu, plus the full dashboard at `/p/ai-models/` on stayhungryasi.com. It is NOT a research-library entry (do not create `_source/research/ai-model-effort-matrix/`). Lives in `_source/pipelines/ai-model-effort-matrix/`. Run all commands from this folder. Everything here is public; never add private wording to these files.

Outputs (repo root): `p/ai-models/index.html` (full Korean dashboard, standalone page), `live/models.json` (read by the reader page, 4 languages) and `data/models.json` (open data API, same content). Both JSON files are pipeline-owned (`bot_owned` in apiData), so `build.py` never writes them.

## Files
| File | Role |
|---|---|
| `aa_v6.py` | Artificial Analysis (AA) Intelligence Index v5.0.1 rows: Anthropic + Google + Meta + other labs, per effort level |
| `aa_v6_gpt.py` | OpenAI rows |
| `compute_v6.py` | Model list (META), task weights, scoring, recommendations → `data6.json` |
| `build6.py` | Text (findings, notes, sources) + `head6.html` + `body6.html` → page. `--page` = standalone document for /p/ai-models/ (title, canonical, og), `--out FILE` |
| `check6.py` | Pre-publish checks. Exit 1 = do not publish |
| `make_live.py` | Reader-page/API summary → `live/models.json` + `data/models.json` (every number computed from `data6.json`) |
| `head6.html`, `body6.html` | Page styles and layout/JS |
| `data6_prev.json` | Last published data (for month-over-month comparison) |

## Monthly procedure
1. **Ruler check.** Open https://artificialanalysis.ai/methodology/intelligence-benchmarking. If the index version is no longer v5.0.x, or the benchmark list or weights changed: STOP, do not publish, and report what changed (the task mapping must be redesigned by a person).
2. **New models.** Check https://artificialanalysis.ai/leaderboards/models (top 40) and the vendors' news pages (Anthropic, OpenAI, Google, Meta, xAI, DeepSeek, Moonshot, Alibaba, Tencent, Mistral). Add any model that enters the AA top 40 or is a new flagship of a listed vendor; drop models AA no longer lists. New model = new META line in `compute_v6.py` (id, label, vendor, group, price, open weights, release date, app default, note).
3. **Fetch rows.** For every model in `aa_v6.py` / `aa_v6_gpt.py`, refetch AA comparison pages (`/models/comparisons/<a>-vs-<b>`, e.g. `claude-fable-5-2-low-vs-claude-fable-5-2-xhigh`, `...-medium-vs-...-high`, and a max pairing). Confirm each page says v5.0.x; AA serves stale cached pages — append `?nocache=<date>` when a page shows GDPval/SciCode/LCR (v4) columns. Record: ii, brief, auto, gdppdf, fc, tb4, tbsci, crit, omni, hled, cost, out, speed, e2e, time.
4. **Cross-check.** Fetch three combos a second time from a different comparison page (the current #1, the Claude value pick, the cheapest frontier point). Index and benchmark values must match exactly; cost within 3%, time within 10%.
5. **Compute + check.** `python3 compute_v6.py && python3 check6.py --prev data6_prev.json`. Any ERROR → STOP, report, do not publish. WARNINGs about index moves ≥6 must be explained in the findings.
6. **Text.** Most findings are computed from data, but `build6.py` also has hand-written sentences (EXTRA, effNotes, newRel, verdicts, support, uncert, sources). Re-read every one against the new data and sources; rewrite anything no longer true; add the month's new releases to `newRel` (keep the last ~10); mark reversed conclusions with an `["x","정정", ...]` finding.
7. **Build.** `python3 build6.py --page --out ../../../p/ai-models/index.html`, then `python3 check6.py ../../../p/ai-models/index.html`. The header carries the stayhungryasi.com logo (outlined SVG inside `body6.html`; master files in `assets/brand/`).
8. **Reader summary.** `python3 make_live.py ../../..` (writes `live/models.json` and `data/models.json`). The reader-page text is in `_source/page.html` (`MDX` dictionary, en/ko/es/ja) and only formats these numbers; if the JSON shape changes, update `rModels()`, the dev-view `models(t)` file and the `models` chat command too. Spot-check that the leader, the cost-switch % and the 5 task picks match the dashboard.
9. **Publish** with the stayhungry-hub-update procedure: changelog entry (4 languages, `"h":"HEAD"`), regenerate `_source/template.html`, build to a scratch dir, copy outputs (never crisis.json / fear.json / models.json — build.py skips them), Playwright screenshots of `#models` and `/p/ai-models/` (1440×900, 1280×760, 390×860; ko/en/es/ja), forbidden-term scan, commit, `git fetch` + rebase, push, pin the changelog hash, verify live (`/live/models.json` shows the new `asof`, `/p/ai-models/` shows the new 기준일).
10. **Archive.** Copy the new `data6.json` to `data6_prev.json` in the same commit.
11. **Report** (Korean, to the site owner): what changed this month (new models, rank changes, recommendation changes), anything that stopped the run, and unverifiable items.

## Guardrails
- Never publish numbers that were not read from an AA page this run. If a model's page cannot be fetched, keep last month's row only if AA still lists the same values on its leaderboard; otherwise drop the model and say so.
- Scores are a weighted mapping of AA benchmarks (estimates); say so on the page.
- Credit line: stayhungryasi.com

## Four languages (since 2026-11-14)

The dashboard is published in Korean (`/p/ai-models/`) plus English, Spanish and Japanese (`/p/ai-models/en/`, `/es/`, `/ja/`).

After step 7 (build + check), always run:

```
python3 translate6.py ../../../p/ai-models/index.html
```

- `seg6.py` finds every piece of Korean text in the built page; `tr6.json` maps each piece to `{en, es, ja}`.
- A piece with no translation stops the run and is listed. Add it to `tr6.json` and run again. Sentences that carry this month's numbers are new every month, so expect a few dozen. Rules: same numbers, same `${...}` expressions and `\n` escapes, no raw double quotes inside a translation, hub wording (ja 思考量 / 業務 / コスパ, es esfuerzo / área / valor, levels as in `tr6.json`).
- The script also adds the language bar, hreflang links and the language redirect to the Korean page (safe to run twice).
- Check: open all 8 tabs in each language, no Korean left, no console errors, charts drawn.
- The hub links to the edition of the reader's language (`mdUrl()` in `_source/page.html`); the sitemap lists all four (`_source/build.py`).
