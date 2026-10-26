# Build and typecheck the package

`npm run build` compiles `src/index.ts` to `dist/` (ESM + CJS + `.d.ts`) via tsup; `npm run typecheck` runs `tsc --noEmit`. Every other verification drive depends on these: the library surface, `render-hde.mjs`, `test-render.mjs`, and the PNG pipeline all import from `dist/`.

## Sub-features

- `build-esm` produces `dist/index.mjs` (ESM).
- `build-cjs` produces `dist/index.js` (CJS).
- `build-dts` produces `dist/index.d.ts` / `dist/index.d.mts` (types).
- `typecheck` confirms all TypeScript in `src/` compiles without emit.

## How to get to it (user POV)

- `npm run build` — compile the package.
- `npm run typecheck` — type-check without emitting.
- The control CLI runs `npm run build` inside `doctor`, so a green `doctor` already implies a successful build.

## Driving it with npm

Preconditions:

- Node v22.x and `npm` on PATH (this box: node v22.22.2, npm 10.9.7).
- `node_modules/` installed (`npm install` if `node_modules` is missing).

- **Build.** Run `npm run build`. Exit 0; tsup output ends `DTS ⚡ Build success in ~1.5s`; `dist/index.mjs`, `dist/index.js`, `dist/index.d.ts` all exist.
- **Verify exports.** Run `node -e "import('./dist/index.mjs').then(m => console.log('EXPORTS:', Object.keys(m).join(', ')))"`. Stdout is `EXPORTS: BodyGraph, renderToSVG`.
- **Typecheck.** Run `npm run typecheck`. Exit 0, no output (tsc is silent on success).
- **Typecheck failure shape.** (Adversarial, for the proof bar) temporarily rename `src/renderer.ts` to `src/renderer.ts.bak`, run `npm run typecheck` (exit non-zero with `Cannot find module './renderer'`), then restore. This is the "adversarial doctor" equivalent for the build surface.

## Gotchas

- `npm run build` is **not** a no-op when `dist/` is up to date — it recompiles every time (~2s). Re-running after any `src/` edit is the safe move, not an optimization.
- tsup externalizes `react` (peer dependency) — it is not bundled into `dist/`. A consumer without React will fail at import, not build.
- `dist/` is gitignored build output (package `files: ["dist"]` controls npm publish, not git). A fresh clone has no `dist/` until the first `npm run build`.
- `npm run dev` is the watch variant — never use it in a verification run (it never exits).
