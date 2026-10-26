# Screenshot an SVG to PNG

`npm run screenshot` (scripts/screenshot.js) renders the fixture's SVG to a raster PNG using Playwright, by loading the SVG into a headless Chromium page and screenshotting the `<svg>` element at its natural bounding box. It is the bridge from the SVG world to the pixel-diff pipeline.

## Sub-features

- `shot-render-svg` re-renders `reference/test-chart.json` via the library and writes `output/current.svg`.
- `shot-render-png` screenshots the SVG element to `output/current.png` (or a passed path).
- `shot-fail-nobrowser` without installed Playwright browsers, exits 1 with a clear install hint.

## How to get to it (user POV)

- `npm run screenshot` — writes `output/current.png` (and `output/current.svg`).
- `npm run screenshot output/other.png` — custom output path.
- Requires the Playwright Chromium browser binary installed: `npx playwright install chromium` (or `npx playwright install`).

## Driving it with node

Preconditions:

- `npm run build` exited 0 (imports `dist/index.js` — the **CJS** build).
- Playwright Chromium installed (`npx playwright install`). **Not yet installed on this box** — see Gotchas.

- **Run (when browser present).** Run `npm run screenshot`. Exit 0; `output/current.svg` and `output/current.png` exist; the PNG is the SVG rendered at its natural size.
- **Custom path.** Run `npm run screenshot /tmp/my.png`. Exit 0; `/tmp/my.png` exists.
- **Run (browser absent, current box state).** Run `npm run screenshot`. Exit 1; stderr: `screenshot.js failed: browserType.launch: Executable doesn't exist at ~/.cache/ms-playwright/...` plus the Playwright install hint.

## Gotchas

- **Unreachable on this box without setup:** the Playwright browser binary is not installed (verified 2026-10-26: `Executable doesn't exist at /home/ubuntu/.hermes/profiles/orchestrator/home/.cache/ms-playwright/chromium_headless_shell-1217/...`). First run `npx playwright install chromium` or report the feature unreachable with that exact error.
- The pre-existing `output/current.png` (177 KB, from May 30) is **stale** — it predates the current build. Never treat it as proof of the current renderer; a verification run must produce a fresh one.
- Imports `dist/index.js` (CJS), not `dist/index.mjs` — a broken CJS build fails here even if ESM works.
- The SVG is rendered into a minimal HTML wrapper with a `#f5ead8` background; the PNG includes that background, so pixel diffs against a transparent-background reference will differ across the whole canvas.
