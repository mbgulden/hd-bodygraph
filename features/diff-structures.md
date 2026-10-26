# Diff extracted structures

`npm run diff-structures` (scripts/diff-structures.js) compares two geometry-extraction JSONs — `output/reference-structure.json` (measured from the reference image) against `output/rendered-structure.json` (measured from the live render) — and writes `output/structural-diff.json` with exact percentage deltas and `apply-fixes`-parseable fix suggestions. It is the precision half of the refinement pipeline (no API key, fully offline).

## Sub-features

- `ds-run` diffs the two structure JSONs and writes `output/structural-diff.json`.
- `ds-score` computes an overall score (0–10) from the deltas; the report includes `score`, `critical_count`, `minor_count`, `viewbox`, and `diffs[]`.
- `ds-gate` exits 0 when score ≥ 8, else 1.
- `ds-fixes` each `diffs[]` entry carries `element`, `issue`, `fix` (e.g. `shift gate 41: x+=0.00% y+=-4.60%`), and `severity` (`critical` | `minor`).

## How to get to it (user POV)

- `npm run diff-structures` from the repo root (no arguments, no env).
- Inputs must already exist: `output/reference-structure.json` (from the one-time `extract-reference.js` vision step) and `output/rendered-structure.json` (from `extract-rendered.js`, which needs Puppeteer Chrome + `data-*` attributes on the SVG).
- Output feeds `apply-fixes` in precision mode.

## Driving it with node

Preconditions:

- Both `output/reference-structure.json` and `output/rendered-structure.json` exist (they do on this box, from a prior pipeline run — May 30).
- No network, no API key, no browser — pure JSON computation.

- **Run.** Run `node scripts/diff-structures.js`. Exit 0 (score ≥ 8). The report is rewritten to `output/structural-diff.json`; for the current pair of structure files it reads `{"score": 9, "critical_count": 0, "minor_count": 2, ...}` with two diffs: `CENTER_Head` height off by 6.8% (minor) and `GATE_41` position off by dy=-4.6% (minor).
- **Inspect output.** `python3 -c "import json; d=json.load(open('output/structural-diff.json')); print(d['score'], d['critical_count'], d['minor_count'])"` prints `9 0 2`.
- **Missing input (negative path).** Move `output/rendered-structure.json` aside and re-run. Exit 1; stderr: `No rendered-structure.json. Run extract-rendered.js first.` Restore the file afterwards.
- **Determinism.** Re-run twice; `sha256sum output/structural-diff.json` is identical between runs (pure function of the two inputs).

## Gotchas

- **It overwrites `output/structural-diff.json`** — which `apply-fixes` (precision mode) and `refine-loop` both read. A verification run that diffs fresh inputs invalidates the fix list a prior `apply-fixes` used. If the file is tracked in git, `git checkout -- output/structural-diff.json` to restore the tracked baseline.
- **Inputs are stale by default:** the structure JSONs on this box are from a prior run (May 30) and correspond to that run's geometry. After any `src/geometry.ts` change, `rendered-structure.json` is out of date until `extract-rendered.js` (Puppeteer) regenerates it — a diff run on stale inputs proves nothing about the current code.
- Thresholds are hardcoded in the script (center position 2%, center size 3%, gate 3% of image dims): deltas below a threshold are ignored, not reported.
- The score is 0–10 and the gate is ≥ 8 — a score of 8 with one critical and ten minor passes the same as a score of 9 with two minor. Read `critical_count`, not just the score.
- `extract-reference.js` (the source of the reference JSON) is a **one-time vision-API script** — regenerating the reference requires `ANTHROPIC_API_KEY` and a reference image.
