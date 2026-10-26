# Render with the HDE color scheme

`render-hde.mjs` renders a chart the way the HDE (Human Design Engine) product shows it: it uses the **library** `renderToSVG` from `dist/` but forces per-center defined colors (matching the Neutrino Design reference) and per-channel Design/Personality coloring (red = design, black = personality, deep red = both, amber = mixed), plus gate numbers, center labels, activation columns, and body silhouette.

## Sub-features

- `hde-render` renders a fixture through the library build with the HDE-style overrides.
- `hde-channel-coloring` colors each channel by the stream mix of its two gates.
- `hde-theme-arg` accepts a theme preset as the second positional, defaulting to `canonical`.

## How to get to it (user POV)

- `node render-hde.mjs <chart.json> [theme]` from the repo root; SVG prints to stdout.
- Redirect to a file: `node render-hde.mjs reference/test-chart.json canonical > out.svg`.

## Driving it with node

Preconditions:

- `npm run build` exited 0 (this script imports `./dist/index.mjs`, unlike `render-cli.mjs`).
- Fixture `reference/test-chart.json` exists.

- **Render.** Run `node render-hde.mjs reference/test-chart.json canonical > /tmp/hde.svg`. Exit 0; the SVG begins `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 900"` — the **library** geometry, confirming it is not the standalone `render-pro.mjs` path.
- **Overrides visible.** Grep the output: it contains `showGateNumbers`-style gate number text (each gate number appears as text), center label text, and channel strokes using the HDE palette (`#e53935`, `#1a1a1a`, `#b71c1c`, `#e65100`).
- **Theme arg.** Run with `dark`. Exit 0; the SVG carries the dark background fill while keeping the 820×900 viewBox.
- **Usage error.** Run `node render-hde.mjs` (no args). Exit 1; stderr is `Usage: node render-hde.mjs <chart.json> [theme]`.

## Gotchas

- The channel coloring derives from `designGates`/`personalityGates`/`bothGates` arrays on the chart. A fixture that only supplies the unified `gates` array (like `reference/test-chart.json`) still renders, but the per-stream coloring logic only sees the three separate arrays — check the fixture shape before asserting a specific channel color.
- Because it imports `dist/`, a stale build silently renders with the old library — re-run `npm run build` after any `src/` change before comparing.
- Identical argument shape to `render-cli.mjs` but a different renderer (library vs standalone). Name the script in every proof.
- The center colors hardcode the Neutrino reference palette; they override whatever the theme preset would give the centers.
