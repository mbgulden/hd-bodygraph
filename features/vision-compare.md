# Vision-compare render to reference

`npm run vision-compare` (scripts/vision-compare.js) sends up to three images (current render, reference, pixel diff) to the Claude vision API and receives structured JSON with coordinate patch suggestions. It writes `output/vision-comparison.json` and gates on the model's similarity score (pass ≥ 8).

## Sub-features

- `vc-run` sends `output/current.png` (+ `reference/target.png`, `output/diff.png` if present) to Claude vision.
- `vc-output` writes `output/vision-comparison.json` with structured issues and fix suggestions.
- `vc-gate` exits 0 when the vision score ≥ 8, else 1.
- `vc-nosecret` without `ANTHROPIC_API_KEY`, exits 1 immediately.

## How to get to it (user POV)

- `ANTHROPIC_API_KEY=<key> npm run vision-compare` from the repo root.
- The key comes from the environment only — never hardcode, never echo it.
- Inputs must already exist: run `npm run screenshot` (or `render-png`) and `npm run pixeldiff` first.

## Driving it with node

Preconditions:

- `ANTHROPIC_API_KEY` set in the environment.
- `output/current.png` exists (from `screenshot` or `render-png`).
- Optional: `reference/target.png`, `output/diff.png`, `output/diff-stats.json`.
- `@anthropic-ai/sdk` installed (it is, dev dependency).

- **No key (negative path, no network).** Run `env -u ANTHROPIC_API_KEY node scripts/vision-compare.js`. Exit 1; stderr exactly: `ANTHROPIC_API_KEY env var is required`.
- **With key (happy path).** Run `ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" node scripts/vision-compare.js`. Exit 0 or 1 depending on score; `output/vision-comparison.json` exists and is valid JSON containing a score and an `issues` array; each issue carries a `fix` string in `apply-fixes`-parseable form (e.g. `shift gate 44: x+=-2.3% y+=1.1%`).
- **Missing input.** Without `output/current.png`, run with the key. Exit 1; stderr names the missing file.

## Gotchas

- **Requires a live Anthropic API key** — this is the one feature in the map that spends money per run. On a cost-sensitive box (Michael's standing preference), run it only when the pixel-diff gate has already failed and human eyes can't resolve it.
- The vision call is **non-deterministic**: two identical inputs can yield different issue lists and scores across runs. Never use a vision score as a regression baseline — use pixel-diff/sha for that, vision for *diagnosis*.
- The model is pinned in the script (`claude-opus-4-6`); an upstream model retirement silently changes behavior. Check the script's model string before trusting a score.
- Fix suggestions are *proposals* for `apply-fixes`, not applied changes. A green `vision-compare` exit does not modify `src/`.
