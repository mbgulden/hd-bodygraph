# Apply coordinate fixes

`npm run apply-fixes` (scripts/apply-fixes.js) reads a diff file and patches coordinates in `src/geometry.ts` directly — it is the mutation step of the refinement pipeline. It supports three input formats: `output/structural-diff.json` (precision pipeline), `output/vision-comparison.json` (vision pipeline), and, with no argument, the legacy `output/comparison.json`.

## Sub-features

- `af-structural` (first arg = `output/structural-diff.json`) parses `diffs[].fix` strings like `shift gate 44: x+=-2.3% y+=1.1%`.
- `af-vision` (first arg = `output/vision-comparison.json`) parses `issues[].fix` strings in the same form.
- `af-legacy` (no arg) parses `specific_fixes[]` from `output/comparison.json`.
- `af-report` prints each parsed fix and whether it auto-applied or needs manual review; unparseable fixes are reported, not silently dropped.

## How to get to it (user POV)

- `npm run apply-fixes output/structural-diff.json` (precision mode)
- `npm run apply-fixes output/vision-comparison.json` (vision mode)
- `npm run apply-fixes` (legacy mode)

## Driving it with node

Preconditions:

- A diff file from `diff-structures` / `vision-compare` / `compare` exists in `output/`.
- **Clean git state for `src/`** — this script rewrites `src/geometry.ts`. Verify with `git status --short src/` before, and have `git checkout -- src/geometry.ts` ready as the rollback.

- **Structural mode (verified on this box).** Run `node scripts/apply-fixes.js output/structural-diff.json`. Exit 0; stdout lists each fix, e.g. `Fix: shift gate 41: x+=0.00% y+=-4.60%` and a `⚠ Could not auto-apply fix:` line for patterns the parser doesn't handle. **Verify the mutation:** `git diff src/geometry.ts` — for the current `output/structural-diff.json` the applied change was gate 41 `y: 730` → `y: 700` (computed from the 820×650 viewbox constants in the script).
- **Rollback (required after a trial run).** Run `git checkout -- src/geometry.ts`, then `npm run build`. Confirm the renderer is byte-identical to baseline: re-render `reference/test-chart.json` canonical and check sha256 is `273ce86f3f67349a92a95ab3a6c1c4fd58bcb35d2d1f0c7afce983989c2bc253`.
- **No input (legacy mode, missing file).** With no `output/comparison.json`, run `node scripts/apply-fixes.js`. Exit 1; stderr names the missing file. (The file exists on this box from a prior run — move it aside to test.)
- **Rebuild after any applied fix.** Run `npm run build` and re-run a render drive; the geometry change only takes effect through the rebuilt `dist/`.

## Gotchas

- **It mutates `src/geometry.ts` for real.** A green exit does not mean "review requested" — applied fixes are written to the file immediately. Never run this on a dirty or uncommitted `src/`; always `git status --short src/` first, `git checkout` after a trial, and `npm run build` to verify the baseline hash returned.
- **Unparseable fixes are not fatal:** `⚠ Could not parse fix automatically` / `Could not auto-apply fix` lines still leave exit 0. A run that "applied" nothing looks identical to one that applied everything — read the per-fix lines.
- **Viewbox constants are hardcoded** in the script (820×650 reference frame) and must match `src/geometry.ts`; if the geometry's coordinate space changes, the computed pixel deltas are wrong even when the JSON is valid.
- The legacy (no-arg) mode reads `output/comparison.json`, which the `compare` feature writes — the file is a pipeline artifact, not a fixture. Don't hand-edit it to test.
