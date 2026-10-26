# Render the two-theme test fixture

`test-render.mjs` is the package's own end-to-end render entrypoint: it reads the standing fixture, renders it twice (canonical and default themes) through the **library** build, and writes both SVGs to `output/`. It is the fastest way to prove the whole library path works with real data in one command.

## Sub-features

- `tr-render-canonical` renders the fixture with `theme: 'canonical'` to `output/test-bodygraph.svg`.
- `tr-render-default` renders the same fixture with `theme: 'default'` to `output/test-bodygraph-default.svg`.
- `tr-report` prints the SVG length to confirm a non-trivial render.

## How to get to it (user POV)

- `node test-render.mjs` from the repo root.
- No arguments, no flags, no environment — fully self-contained.

## Driving it with node

Preconditions:

- `npm run build` exited 0 (imports `./dist/index.mjs`).
- `reference/test-chart.json` exists.

- **Run.** Run `node test-render.mjs`. Exit 0; stdout:
  ```
  Rendered to output/test-bodygraph.svg
  SVG length: 35293 chars
  Default theme also rendered
  ```
- **Verify outputs.** `ls -la output/test-bodygraph*.svg` shows both files, each ~35 KB. `grep -o 'viewBox="[^"]*"' output/test-bodygraph.svg` prints `viewBox="0 0 820 900"`.
- **Theme difference.** `cmp output/test-bodygraph.svg output/test-bodygraph-default.svg` reports the files differ (canonical vs default theme markup); both carry the 820×900 viewBox.
- **Determinism.** Re-run `node test-render.mjs` and `sha256sum output/test-bodygraph.svg` twice. The hash is identical across runs (deterministic render).

## Gotchas

- This script **overwrites** `output/test-bodygraph.svg` and `output/test-bodygraph-default.svg` on every run — treat those files as ephemeral build output, not proof artifacts. Copy them into `skills/verify-hd-bodygraph/evidence/` if they must survive cleanup.
- It imports `dist/`, so a stale build proves the old renderer. Re-run `npm run build` first if `src/` changed.
- Only two themes are exercised here; the other three presets (`minimal`, `dark`, `light`) are covered by the [render-to-svg](./render-to-svg.md) feature.
- The `output/` directory is created on demand; a clean checkout without `output/` still works.
