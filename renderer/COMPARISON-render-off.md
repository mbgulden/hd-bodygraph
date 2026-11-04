# RENDER-OFF — same fixtures through both existing renderers (SPEC §5.1)

Task: t_97e70f92 · Date: 2026-11-04 · Worker: ned
Fixtures: `michael-data.json` (Vector #1, box fixture) and `reference/test-chart.json` (Generator, 5 channels, string-activation format)
Artifacts (saved, reproducible):

| renderer | command | output |
|---|---|---|
| render-pro.mjs (production path, 820×960) | `node render-cli.mjs michael-data.json` | `output/render-off/renderpro-michael.svg` (38,847 B) |
| render-pro.mjs | `node render-cli.mjs reference/test-chart.json` | `output/render-off/renderpro-test.svg` (24,258 B) |
| library `src/renderer.ts`+`geometry.ts` (820×900), freshly rebuilt `npm run build` | `node render-hde.mjs michael-data.json canonical` | `output/render-off/library-michael.svg` (33,577 B) |
| library | `node render-hde.mjs reference/test-chart.json canonical` | `output/render-off/library-test.svg` (35,345 B) |

## Per-dimension comparison (SPEC §5.1: viewBox, palette, shapes, gate positions, channel paths, activation rendering)

| dimension | render-pro.mjs | library (src/renderer.ts) |
|---|---|---|
| viewBox | 820×960 | 820×900 |
| center palette (defined fills) | per-center set from its own palette constants (Neutrino-matching) | canonical theme = CEN-07 table (also Neutrino-matching; `CANONICAL_CENTER_COLORS`); default theme = single tan `#C9956A` |
| center shapes/positions | hardcoded 9 shapes | `geometry.ts` 9 shapes (positions match parent-task geometry JSON within rescale) |
| gate positions | hardcoded 64 (all present) | 64 (all present) |
| channel table | **35 pairs — missing 10–34 Exploration (G–Sacral)** (CHN-01 E-tier) | **35 pairs — same missing 10–34** (CHN-01 E-tier); parent-task geometry JSON (d0bb8c0) is the 36/36 source |
| channel rendering | polygons (parallel paths for mixed activations) | path/line strokes per circuit |
| activation columns | consumes `{gate,line,color,tone,base}` objects natively — renders | **renders literal `[object Object]` text on both real fixtures** (expects `"26.3"` strings; every real input shape carries objects) |
| both-side gates | parallel red+black lines (no single third fill) | `bothFill #8b5cf6` purple in DEFAULT theme (CHN-06 E-tier FAIL if shipped) |
| input contract | box fixture shape only | `ChartData` type (strings) — no fixture/corpus compatibility |
| provenance/evidence | production wiring only | verify skill evidence pack + types + React component |

Note: `reference/demo.py` referenced in an earlier draft does not exist on the box (checked repo + git history); the SPEC §5.1 pair is render-pro.mjs vs the library renderer, as Jimmy's re-scope comment states.

## Decision (SPEC §5.3, recorded in writing)

**Neither existing renderer is canonical.**
- Library renderer (default candidate) fails §3/§6 bar on real data: [L1] `[object Object]` activation columns on both fixtures; [L2] 35/36 channel pairs; [L3] purple bothFill.
- render-pro.mjs fails [R1] 35/36 channel pairs (independently).
- §5.3 authorises a from-scratch renderer where both fail. Evidence above is the record.

**Canonical renderer: `renderer/render_bodygraph.py`** (this task's deliverable):
- pure function, stdlib-only, no dependencies beyond the chart object (acceptance 3)
- 36/36 channel pairs (CHN-01) — verified against `geometry/bodygraph_geometry.json` (d0bb8c0) by `scripts/verify_renderoff.py` check 7b/7c
- CEN-07 palette, Spleen teal border (CEN-08 lock recorded in the module header)
- both-side gates split black/red, no third color (CHN-06)
- consumes all three real input shapes: box fixtures, corpus `expected`, SPEC §3 public payload

## Retirement (SPEC §5.3 — "two live renderers after this task is a failed acceptance criterion")

- `render-cli.mjs`→`render-pro.mjs`: **DEPRECATED** (header note added 2026-11-04). Existing reports-service wiring keeps calling it until the G4 page swap; it gains no new features.
- TS library (`src/` + `dist/`): retained as the reusable **React component** for in-app/interactive surfaces (§7 v1.5 layer), not as a second server-side chart renderer. Its [L2] 35/36 and [L3] purple-bothFill defects are recorded here; they must be fixed in the library before it ships any activated-chart output.
- Net: exactly **ONE canonical server-side chart renderer** is live: `renderer/render_bodygraph.py`.

## Verification

```
python3 renderer/render_bodygraph.py           # → renderer/demo-vector1.svg
python3 scripts/verify_renderoff.py            # 20 PASS / 0 FAIL
```
20-check verifier: XML parse, 9 center shapes, CEN-07 fills, 64 gate pills, 26 activation
values (ACT-04 regex), ACT-01 column sides, CHN-06 split/no-purple, CHN-03 defined-channel
count, LBL-06/09 text hygiene, CHN-01 36/36 pair equality vs geometry JSON + CEN-04 center
consistency, and the Jimmy 06:10 census (9 centers / 64 gate labels / 36 channel geometries).
ACT-06 additionally confirmed: both columns read the exact SPEC §6 sequences
(Personality 26.3→1.4; Design 47.5→44.6) — separate check, both True.
