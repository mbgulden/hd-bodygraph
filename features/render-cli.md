# Render a chart from the CLI

`render-cli.mjs` is the standalone command-line renderer: point it at a `ChartData` JSON file and a theme, and it prints a complete SVG bodygraph to stdout. It imports `render-pro.mjs`, a **standalone** renderer — not the library build — so its output geometry (viewBox `0 0 820 960`) differs from `renderToSVG` (viewBox `0 0 820 900`).

## Sub-features

- `cli-render` renders a fixture file to an SVG on stdout (exit 0).
- `cli-theme` accepts a theme name as the second argument, defaulting to `canonical`.
- `cli-usage-error` with no arguments exits 1 and prints usage to stderr.
- `cli-render-fail` on an unreadable/invalid file path exits 1 with a message.

## How to get to it (user POV)

- `node render-cli.mjs <chart.json> [theme]` from the repo root.
- Redirect stdout to a file: `node render-cli.mjs reference/test-chart.json canonical > out.svg`.
- The control CLI drives this exact path: `python3 scripts/control-hd-bodygraph.py drive cli`.

## Driving it with node

Preconditions:

- No build required — this path does not touch `dist/`.
- Fixture `reference/test-chart.json` exists.

- **Render.** Run `node render-cli.mjs reference/test-chart.json canonical > /tmp/cli-canonical.svg`. Exit 0; the file begins `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 960"`; stdout itself is empty (SVG went to the file).
- **Theme default.** Run `node render-cli.mjs reference/test-chart.json > /tmp/cli-default.svg`. Exit 0; `theme` defaulted to `canonical`, so this SVG is byte-identical to the explicit-canonical one (`cmp` reports no differences).
- **Usage error.** Run `node render-cli.mjs` (no args). Exit 1; stderr is exactly `Usage: node render-cli.mjs <chart.json> [theme]`; stdout empty.
- **Bad file.** Run `node render-cli.mjs does-not-exist.json`. Exit 1; stderr starts `Render failed:`.
- **Control-CLI path.** Run `python3 scripts/control-hd-bodygraph.py drive cli`. Exit 0; JSON output reports `"surface": "CLI (render-cli.mjs → render-pro.mjs)"`, `"viewBox": "0 0 820 960"`, and `evidence/cli-canonical.svg` is written.

## Gotchas

- **Different renderer, different geometry:** `render-cli.mjs` uses `render-pro.mjs` (viewBox `0 0 820 960`), while `renderToSVG` from `dist/` uses `0 0 820 900`. Any fixture diff across these two surfaces always differs — name which surface a proof uses.
- The SVG goes to **stdout only**; the script writes no files itself. "Exit 0" with no captured output proves nothing.
- Theme is a positional string, not a flag. `node render-cli.mjs chart.json --theme canonical` treats `--theme` as the file path's theme argument position — the CLI has no flag parsing at all.
- `render-hde.mjs` has an identical argument shape (`node render-hde.mjs <chart.json> [theme]`) but uses the **library** build — don't confuse the two in a diff.
