# Run the refine loop

`npm run refine` (scripts/refine-loop.sh) is the autonomous visual refinement pipeline: it loops `render SVG → Playwright screenshot → pixelmatch diff → Claude vision (3 images) → apply-fixes → rebuild` until the pixel diff drops below 5%, the vision score reaches ≥ 8, or a maximum of 6 iterations is hit. It bootstraps a reference image from the first render if none exists.

## Sub-features

- `ref-loop` iterates the render→diff→vision→fix→rebuild cycle.
- `ref-bootstrap` with no `reference/target.png`, copies the first render as the reference (and warns).
- `ref-stop-pixel` stops early when `diffPct < 5`.
- `ref-stop-vision` stops early when the vision score ≥ 8.
- `ref-stop-max` stops at 6 iterations even if neither gate is met.

## How to get to it (user POV)

- `npm run refine` from the repo root.
- `ANTHROPIC_API_KEY=<key> npm run refine` — the key is only needed if a pixel-diff gate is crossed (vision stage).
- `SCRIPTS_DIR` env can relocate the scripts directory (defaults to `scripts`); `MAX_ITERATIONS` is not a CLI flag — it is a constant in the script.

## Driving it with node

Preconditions:

- `npm run build` works (the loop rebuilds each iteration).
- Playwright Chromium **and** Puppeteer Chrome both installed (`npx playwright install` + `npx puppeteer browsers install chrome`) — the loop calls both.
- `ANTHROPIC_API_KEY` in the environment for the vision stage.
- **None of the above are satisfied on this box** (verified 2026-10-26) — see Gotchas before attempting.

- **Dry structure check (no deps needed).** Run `bash -n scripts/refine-loop.sh`. Exit 0 (syntax OK) — proves the script is parseable without running it.
- **Full run (when deps present).** Run `ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" npm run refine`. Stdout shows `=== HD Bodygraph Pixel-Diff Refinement Loop ===`, per-iteration `[1/4] Rendering SVG to PNG (Playwright)...` through `[4/4]`, and a final stop-reason line (pixel threshold / vision score / max iterations). Exit 0 on normal completion.
- **Bootstrap behavior.** With `reference/target.png` deleted, the first run prints `⚠ No reference/target.png found... Bootstrap reference saved to reference/target.png` and the first diff is 0% (comparing a render to itself) — the *second* iteration is the first real comparison.

## Gotchas

- **Unreachable on this box without setup** (verified 2026-10-26): Playwright browsers missing, Puppeteer Chrome missing, `ANTHROPIC_API_KEY` not set. The first failure will be the Playwright `Executable doesn't exist` error at iteration 1, step 1/4.
- **Bootstrap trap:** a bootstrapped reference makes iteration 1's diff trivially 0%, which can stop the loop before any real comparison. If you bootstrapped, delete and regenerate the reference from a *known-good* render, or treat iteration 1's result as void.
- The loop **mutates `src/geometry.ts`** via `apply-fixes` and rebuilds `dist/` on each iteration — it changes the codebase. Run it in a clean git state so a bad fix batch can be `git checkout -- src/`-reverted.
- Each vision iteration spends a paid API call (up to 6× per run).
- Stop conditions are checked *after* each iteration's stages; a mid-iteration crash (e.g. vision API down) kills the loop via `set -e` — check `src/geometry.ts` for a partial fix batch after any crash.
