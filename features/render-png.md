# Render a built-in chart to PNG

`npm run render-png` (scripts/render-png.js) renders the **hardcoded** Maksim chart (defined inline in the script) through the library build to `output/current.svg`, then rasterizes it to `output/current.png` with Puppeteer at an 820×650 viewport, 2× device scale. It is the refinement pipeline's fixed input — the chart is not read from a file.

## Sub-features

- `rp-svg` writes `output/current.svg` from the built-in chart (library render, `renderToSVG(MAKSIM_CHART)` with default theme).
- `rp-png` screenshots the SVG to `output/current.png` (Puppeteer, headless Chrome).
- `rp-fail-nochrome` without an installed Chrome, exits 1 after still writing the SVG.

## How to get to it (user POV)

- `npm run render-png` from the repo root.
- No arguments. The chart is inline; to render a different chart, use `test-render.mjs` or `render-cli.mjs` instead.
- Requires Chrome installed for Puppeteer: `npx puppeteer browsers install chrome`.

## Driving it with node

Preconditions:

- `npm run build` exited 0 (imports `dist/index.js` — CJS build; the error message on failure literally says `Failed to load dist/index.cjs — run npm run build first`).
- Chrome for Puppeteer installed. **Not present on this box** — see Gotchas.

- **Run (Chrome present).** Run `npm run render-png`. Exit 0; stdout:
  ```
  SVG written to output/current.svg
  PNG rendered to output/current.png
  ```
  `output/current.png` is a 1640×1300 PNG (820×650 viewport @ 2× scale).
- **Run (Chrome absent, current box state).** Run `npm run render-png`. Exit 1; stdout still prints `SVG written to output/current.svg` (the SVG stage completed), then stderr: `render-png failed: Error: Could not find Chrome (ver. 127.0.6533.88)...` with install hint.
- **SVG stage is independently verifiable.** Even without Chrome, `output/current.svg` is written and can be checked: `grep -o 'viewBox="[^"]*"' output/current.svg` → `viewBox="0 0 820 900"`.

## Gotchas

- **Partial-success exit:** the script writes the SVG *before* launching Chrome, so a Chrome failure (exit 1) still leaves a fresh `output/current.svg`. Don't read "SVG written" in stdout as full success — the exit code is the gate.
- **The chart is hardcoded** (`MAKSIM_CHART` literal in the script) — it does NOT read `reference/test-chart.json`. If a proof needs the fixture chart, use `test-render.mjs` or the library render; if it needs the pipeline's canonical input, use this.
- Overwrites `output/current.svg` and `output/current.png` — both are shared inputs to `pixeldiff` and `screenshot`. Re-run after any renderer change.
- Imports `dist/index.js` (CJS). A broken CJS build fails here even if the ESM build is fine.
- Unreachable as a PNG feature on this box until `npx puppeteer browsers install chrome` (verified 2026-10-26: `Could not find Chrome`).
