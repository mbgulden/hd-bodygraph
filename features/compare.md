# Compare a render against a reference

`npm run compare` (scripts/compare.js) is the older reviewer-vision gate: it sends the current render PNG to Claude with a rubric of what a correct HD bodygraph looks like (center shapes, channel routing, gate placement, labels) and asks for a structured review. It writes `output/comparison.json`.

## Sub-features

- `cmp-run` sends `output/current.png` to the vision model with the bodygraph correctness rubric.
- `cmp-output` writes `output/comparison.json` with the model's review (score + `specific_fixes`).
- `cmp-nosecret` without `ANTHROPIC_API_KEY`, exits 1 immediately.

## How to get to it (user POV)

- `ANTHROPIC_API_KEY=<key> npm run compare` from the repo root.
- Requires `output/current.png` (run `npm run render-png` or `npm run screenshot` first).
- The key comes from the environment only.

## Driving it with node

Preconditions:

- `ANTHROPIC_API_KEY` set.
- `output/current.png` exists.

- **No key (negative path, no network).** Run `env -u ANTHROPIC_API_KEY node scripts/compare.js`. Exit 1; stderr exactly: `ANTHROPIC_API_KEY env var is required`.
- **Missing PNG (no network needed for this check).** Temporarily move `output/current.png` aside, run with the key, and restore. Exit 1; stderr: `output/current.png not found — run npm run render-png first`.
- **With key (happy path).** Run `ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" node scripts/compare.js`. Exit 0; `output/comparison.json` exists, is valid JSON, and contains a review score and a `specific_fixes` array of parseable fix strings (consumable by `apply-fixes` legacy mode).

## Gotchas

- **This is the legacy pipeline's gate** — the newer `vision-compare` (3-image, structured patches) is the preferred path in the refine loop. `compare` matters for verifying the *legacy* branch of `apply-fixes.js` (no-argument mode reads `output/comparison.json`).
- Same non-determinism caveat as vision-compare: vision output varies between runs. Do not baseline on it.
- The model string is pinned in the script (`claude-opus-4-6`); an upstream retirement changes behavior silently.
- Unlike `pixeldiff`, there is **no numeric exit-code gate** on similarity in the sense of a percentage — the exit reflects the model's pass/fail verdict. Two runs on identical input can legitimately differ.
- Costs a vision API call per run; batch it, don't loop it.
