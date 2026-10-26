# HD bodygraph renderer verification map

This directory is the maintained source for verifying the user-facing behavior of **@gonzih/hd-bodygraph** v1.4.1, a Human Design bodygraph SVG renderer. The "user" is a **calling agent or script** that imports the package or runs one of its CLIs. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Work in the box checkout `/home/ubuntu/work/hd-bodygraph` (repo `github.com/mbgulden/hd-bodygraph`).
- Build the artifacts once with `npm run build` (exit 0) and `npm run typecheck` (exit 0). Ready = both pass AND `node -e "import('./dist/index.mjs')"` exposes `BodyGraph, renderToSVG`.
- The standing fixture is `reference/test-chart.json` (parses to a `ChartData` with `definedCenters` + `channels`). A changed fixture invalidates every rendered baseline — record its sha256.
- Put `scripts/control-hd-bodygraph.py` on the path and require `python3 scripts/control-hd-bodygraph.py doctor` to exit 0 before any drive.
- There is **no server and no long-running process** — every drive is an on-demand command in the calling process. Never assume a daemon state.
- The refinement pipeline (`screenshot`, `render-png`, `refine`) needs headless browser binaries (`npx playwright install` / `npx puppeteer browsers install chrome`) and `npm run compare` / `vision-compare` need `ANTHROPIC_API_KEY`. Absent those, those features are unreachable — report them as such, do not paper over with the CLI.

## Driving conventions

- Start every recipe from the built baseline unless its preconditions say otherwise.
- **Name the surface you are proving.** The library (`renderToSVG` via `dist/`, viewBox `0 0 820 900`) and the standalone CLI (`render-cli.mjs` → `render-pro.mjs`, viewBox `0 0 820 960`) are **two different renderers**. A cross-surface SVG diff always differs; a proof must state which entry point it used.
- Prefer stable handles — function names (`renderToSVG`), fixture path, theme names (`canonical`, `default`, `minimal`, `dark`, `light`), and SVG structure (`viewBox` attribute, `data-*` center/gate markup) — not pixel coordinates.
- Run terminal actions through `python3 scripts/control-hd-bodygraph.py drive <target>` where a target exists; otherwise use the literal command in the feature file.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Restore built state after a mutation (re-run `npm run build` if `src/` changed). Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the invocation and the resulting state, not just "no crash": the command, stdout, stderr, and exit code.
- Render proof includes the SVG bytes or file on disk, its `viewBox`, and its sha256 (re-run after a change and compare the hash).
- Deterministic renders ⇒ identical input must produce identical sha256.
- Record the feature ID and entry point used with every artifact.
- Report an unreachable path (missing browser, missing API key) with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with <harness>` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Features

- [Render to SVG via the library](./render-to-svg.md) — the primary `renderToSVG(chart, options)` entry: import, theme presets, overrides, and the deterministic SVG result.
- [Render with the BodyGraph React component](./bodygraph-react.md) — the `BodyGraph` React entry and how to verify it headless.
- [Render a chart from the CLI](./render-cli.md) — `render-cli.mjs`, the standalone renderer, its usage, and its error path.
- [Render with the HDE color scheme](./render-hde.md) — `render-hde.mjs`, library-backed output with Design/Personality channel coloring.
- [Render the two-theme test fixture](./test-render.md) — `test-render.mjs`, the package's own fixture render entrypoint.
- [Build and typecheck the package](./build-typecheck.md) — `npm run build` / `npm run typecheck`, the precondition every other drive depends on.
- [Screenshot an SVG to PNG](./screenshot-png.md) — `npm run screenshot` (Playwright), the bridge from SVG to the pixel-diff pipeline.
- [Pixel-diff two PNGs](./pixeldiff.md) — `npm run pixeldiff`, red-pixel diff image, stats file, and the 5% exit-code gate.
- [Render a built-in chart to PNG](./render-png.md) — `npm run render-png` (Puppeteer), the pipeline's fixed input.
- [Vision-compare render to reference](./vision-compare.md) — `npm run vision-compare`, Claude vision structured output, score gate.
- [Compare a render against a reference](./compare.md) — `npm run compare`, the reviewer-vision gate.
- [Run the refine loop](./refine-loop.md) — `npm run refine`, the autonomous pixel+vision refinement loop and its stop conditions.
- [Apply coordinate fixes](./apply-fixes.md) — `npm run apply-fixes`, patching `src/geometry.ts` from a diff file.
- [Diff extracted structures](./diff-structures.md) — `npm run diff-structures`, comparing reference vs rendered geometry JSON.
