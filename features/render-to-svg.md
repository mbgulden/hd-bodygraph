# Render to SVG via the library

`renderToSVG` is the primary public API of @gonzih/hd-bodygraph: a calling agent passes a `ChartData` object (gates, defined centers, channels, optional activations) and options, and gets back a complete standalone SVG string of the bodygraph. Rendering is deterministic — the same chart and options always produce byte-identical SVG.

## Sub-features

- `lib-import` imports the package from `dist/` and exposes `renderToSVG` + `BodyGraph`.
- `lib-render-canonical` renders a fixture with the `canonical` theme (viewBox `0 0 820 900`).
- `lib-render-themes` renders the same fixture under the five presets (`default`, `canonical`, `minimal`, `dark`, `light`).
- `lib-options-override` applies per-field `BodyGraphOptions` overrides on top of a theme.
- `lib-determinism` re-rendering the same input yields the same sha256.

## How to get to it (user POV)

- `import { renderToSVG } from '@gonzih/hd-bodygraph'` (ESM, `dist/index.mjs`) or `require('@gonzih/hd-bodygraph')` (CJS, `dist/index.js`) after `npm run build`.
- Call `renderToSVG(chartData, options)`; options is optional, `{ theme }` is the most common field.
- The control CLI drives this exact path: `python3 scripts/control-hd-bodygraph.py drive lib`.

## Driving it with node

Preconditions:

- `npm run build` exited 0 and `dist/index.mjs` exists.
- Fixture `reference/test-chart.json` is parseable.

- **Import and list exports.** Run `node -e "import('./dist/index.mjs').then(m => console.log('EXPORTS:', Object.keys(m).join(', ')))"`. Stdout is `EXPORTS: BodyGraph, renderToSVG`.
- **Render canonical.** Run `node -e "import('./dist/index.mjs').then(async m => { const fs = await import('fs'); const chart = JSON.parse(fs.readFileSync('reference/test-chart.json','utf8')); const svg = m.renderToSVG(chart, {theme:'canonical'}); fs.writeFileSync('skills/verify-hd-bodygraph/evidence/lib-canonical.svg', svg); console.log('viewBox:', (svg.match(/viewBox=\"([^\"]+)\"/)||[])[1], 'len:', svg.length); })"`. Exit 0; stdout `viewBox: 0 0 820 900 len: 35293`; an SVG file of 35293 bytes appears on disk.
- **Render every theme.** Loop the same call over `default`, `canonical`, `minimal`, `dark`, `light`. All five exit 0, all five carry `viewBox="0 0 820 900"`; bytes differ per theme.
- **Override a field.** Run the call with `{ theme:'canonical', showCenterLabels:false }`. Exit 0; the output SVG contains no center-label text and a different sha256 than the un-overridden render.
- **Determinism.** Re-run the canonical render and compare `sha256sum` of the two SVGs. The hashes are identical (for this fixture + theme, `273ce86f3f67349a92a95ab3a6c1c4fd58bcb35d2d1f0c7afce983989c2bc253`).
- **Control-CLI path.** Run `python3 scripts/control-hd-bodygraph.py drive lib`. Exit 0; stdout is JSON with `"surface": "library (dist/index.mjs renderToSVG)"`, `"viewBox": "0 0 820 900"`, and a `sha256` matching the manual render; `evidence/lib-canonical.svg` is written.

## Gotchas

- This is the **library** renderer (viewBox `0 0 820 900`). `render-cli.mjs` is a different standalone renderer (viewBox `0 0 820 960`) — never diff an SVG across the two surfaces or expect a match.
- Options must be applied after `npm run build`; `dist/` is a build artifact, not source. A stale `dist/` silently proves the old renderer.
- `chartData` must supply `definedCenters` and `channels` (the fixture does); gates can come as a `gates` array or the three `personalityGates`/`designGates`/`bothGates` arrays.
- The return value is a string; nothing is written to disk unless the caller writes it. "No crash" with no output check is not proof.
