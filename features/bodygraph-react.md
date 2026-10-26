# Render with the BodyGraph React component

`BodyGraph` is the package's React entry point: a component that takes a `chart` (plus optional `options`, `className`, `style`) and renders the bodygraph SVG inline via `dangerouslySetInnerHTML`, delegating all drawing to `renderToSVG`. For a verification run the callable behavior is: given props, the component returns a React element whose rendered HTML is the 820×900 SVG.

## Sub-features

- `bg-import` imports `BodyGraph` from the package and confirms it is a function.
- `bg-call-headless` calls `BodyGraph({ chart, options })` without a DOM and inspects the returned element.
- `bg-html-output` confirms the element's inner HTML is the `renderToSVG` output (viewBox `0 0 820 900`).
- `bg-parity` confirms `BodyGraph` output equals `renderToSVG(chart, options)` byte-for-byte.

## How to get to it (user POV)

- `import { BodyGraph } from '@gonzih/hd-bodygraph'` (or CJS `require`) in a React app, then `<BodyGraph chart={chart} options={{ theme: 'canonical' }} />`.
- In a verification run (no React app in this repo), the component can be called as a plain function — `React.createElement` is not required to obtain the element object.
- The `BodyGraph` element is also what `dist/index.d.ts` types as the named export.

## Driving it with node

Preconditions:

- `npm run build` exited 0; `dist/index.mjs` imports cleanly.
- `react` is installed (peer + dev dependency; `node -e "import('react').then(r => console.log(r.version))"` prints the version, e.g. `18.3.1`).
- Fixture `reference/test-chart.json` is parseable.

- **Import and call.** Run `node -e "import('./dist/index.mjs').then(m => { console.log(typeof m.BodyGraph, m.BodyGraph.name); })"`. Stdout is `function BodyGraph`.
- **Headless render.** Run `node -e "Promise.all([import('./dist/index.mjs'), import('fs')]).then(async ([m, fs]) => { const chart = JSON.parse(fs.readFileSync('reference/test-chart.json','utf8')); const el = m.BodyGraph({ chart, options: { theme: 'canonical' } }); const html = el.props.dangerouslySetInnerHTML.__html; console.log('type:', el.type, 'has viewBox:', html.includes('viewBox=\"0 0 820 900\"')); })"`. Exit 0; stdout `type: div has viewBox: true`.
- **Parity with renderToSVG.** In the same call, compare `html === m.renderToSVG(chart, { theme: 'canonical' })`. The comparison is `true` — the component is a thin wrapper over the library renderer.
- **Options pass-through.** Call with `options: { theme: 'minimal' }`. The inner HTML carries the minimal theme's markup (no center fills) and still has the 820×900 viewBox.

## Gotchas

- **Headless limitation:** this checkout has no test harness and `react-dom` is not installed, so the component cannot be mounted to a DOM here. The verifiable contract is the returned element object and its `dangerouslySetInnerHTML.__html`; treat any claim of visual DOM behavior as unverified in this repo.
- `el.type` is the string `div` (the wrapper element type), not a component — assert on `el.props.dangerouslySetInnerHTML.__html`, not on `el.type`.
- Because `BodyGraph` delegates to `renderToSVG`, a regression in the SVG is a regression in this feature too; a green `BodyGraph` call never overrides a red library render.
- `react` is a peer dependency: in a consuming app that doesn't install React itself, the import still resolves here (repo dev-deps) but would fail in a minimal consumer — document the consumer's own dependency requirement.
