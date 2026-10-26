# Pixel-diff two PNGs

`npm run pixeldiff` (scripts/pixeldiff.js) compares two PNG images with pixelmatch: red pixels mark differences, black pixels match. It writes a diff PNG and a stats JSON, and uses the difference percentage as its exit-code gate (pass < 5%).

## Sub-features

- `pd-diff` compares two PNGs, writes the diff image + stats.
- `pd-gate-pass` exits 0 when diffPct < 5%.
- `pd-gate-fail` exits 1 when diffPct ≥ 5%.
- `pd-stats` emits `output/diff-stats.json` with `{ numDiffPixels, totalPixels, diffPct }`.

## How to get to it (user POV)

- `npm run pixeldiff [img1] [img2] [diffOut]` — defaults: `output/current.png` `reference/target.png` `output/diff.png`.
- No network, no API key, no browser — pure computation. Fully self-contained.

## Driving it with node

Preconditions:

- Two PNG files exist. For a self-contained test, use the same file twice (0% diff).
- `pngjs` and `pixelmatch` installed (they are, in `node_modules`).

- **Self-diff (sanity).** Run `node scripts/pixeldiff.js output/current.png output/current.png output/diff-self.png`. Exit 0; stdout:
  ```
  Compared: output/current.png vs output/current.png
  Dimensions: 1640x1300 (img1: 1640x1300, img2: 1640x1300)
  Diff pixels: 0 / 2132000 (0%)
  Diff image: output/diff-self.png
  Stats: output/diff-stats.json
  ```
- **Stats file.** `cat output/diff-stats.json` prints `{"numDiffPixels":0,"totalPixels":2132000,"diffPct":0}`.
- **Different images (gate-fail path).** Render two different-theme SVGs to PNGs (requires browser), diff them, and confirm exit 1 with a high `diffPct`. (Without a browser, the gate-fail path can only be proven by fabricating two different PNGs — acceptable for a structural test, not a renderer test.)
- **Missing input.** Run `node scripts/pixeldiff.js /tmp/nope1.png /tmp/nope2.png`. Exit 1; stderr names the missing file.

## Gotchas

- **Crops to the smaller dimensions:** the comparison crops both images to `min(width1, width2) × min(height1, height2)` from the top-left. Two PNGs of different sizes will not error — they'll silently compare only the overlapping rectangle. Verify dimensions match before trusting a "0% diff" across sizes.
- The 5% gate is hardcoded (`diffPct < 5` → exit 0). A near-perfect render with 4.9% difference passes; 5.1% fails. Tune the threshold in `pixeldiff.js` only if the pipeline contract changes.
- `pixelmatch` v7 is ESM-compiled; the script handles CJS-interop via `_pm.default || _pm` — a naive `require('pixelmatch')` elsewhere in the repo will fail silently (gets the module object, not the function).
- This is a **pure image operation** — it proves nothing about which renderer produced the PNGs. Chain it after `screenshot` or `render-png` to make that link.
