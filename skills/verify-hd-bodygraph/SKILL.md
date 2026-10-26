---
name: verify-hd-bodygraph
description: "Verify @gonzih/hd-bodygraph (Human Design bodygraph SVG renderer) — a library + CLI surface. Use when a change touches src/renderer.ts, src/geometry.ts, or the render CLIs and you need scripted proof that the real render path still produces correct SVG. Launch = npm build + typecheck; Drive = render a fixture chart via the library export and/or the CLI and diff/sha the SVG."
---

# verify-hd-bodygraph

Verification skill for **@gonzih/hd-bodygraph** v1.4.1 — Human Design bodygraph SVG
renderer. Surface: **library** (npm exports `renderToSVG` + React `BodyGraph`) and
**CLI** (`render-cli.mjs`). There is no server: the app runs on demand inside the
calling process. Driving = render a fixture chart and compare the resulting SVG
(sha256 + viewBox + structural spot-checks), plus the package's own test/render
entrypoints.

## Confirmed live facts (verified 2026-10-26, run of t_2235511e)

- Repo: **github.com/mbgulden/hd-bodygraph** — confirmed: `git remote get-url origin`
  (token stripped) = `https://***@github.com/mbgulden/hd-bodygraph.git`.
- Box checkout: **/home/ubuntu/work/hd-bodygraph** — confirmed (git checkout,
  this skill committed on branch `muse/verify-hd-bodygraph`; parent HEAD 636324f).
- Surface: **library/CLI** — confirmed from the live system:
  - No systemd unit and no process serves hd-bodygraph. `systemctl list-units` shows
    HDE services (hde-api, hde-router, …) but none reference this package; the running
    HDE API (`hde-api.service`) has `WorkingDirectory=/home/ubuntu/work/hd-platform`
    — a different checkout, not this library. The package is consumed on demand.
  - `package.json` exports: `.` → `dist/index.mjs` / `dist/index.js` (+ .d.ts).
  - `src/index.ts` public API: `renderToSVG` (from ./renderer) and `BodyGraph`
    (React component), plus type exports. Live probe returns
    `EXPORTS: BodyGraph,renderToSVG`.
  - **Drift (documented, not "fixed"):** `render-cli.mjs` imports `render-pro.mjs`
    (standalone script, viewBox `0 0 820 960`), while the library build
    (`dist/index.mjs` ← `src/renderer.ts` + `src/geometry.ts`) uses viewBox
    `0 0 820 900`. The CLI path and the library path are two different renderers —
    a fixture diff across the two will always differ. Verification must name which
    surface it is proving. This drift is encoded in the control script as
    per-surface expectations (`LIB_VIEWBOX` / `CLI_VIEWBOX`).
  - Node v22.22.2, npm 10.9.7 on this box.
- Known environment gaps (features that are unreachable on this box — see
  `features/` gotchas): Playwright + Puppeteer browser binaries not installed
  (screenshot / render-png / refine-loop); `ANTHROPIC_API_KEY` not set (compare /
  vision-compare); `react-dom` not installed (BodyGraph verified headless only).
- Feature map: **`features/`** (repo root) — `features/README.md` index + 14
  one-file-per-public-entry docs, four-H2 shape each. Index count (14) == files
  on disk (14), mechanically verified.

## Launch

This is a library/CLI: there is no server to keep alive. "Launch" = build the
artifacts once, then run each drive in its own command.

```bash
cd /home/ubuntu/work/hd-bodygraph
npm run build       # tsup src/index.ts → dist/ (esm+cjs+dts). exit 0 = ready.
npm run typecheck   # tsc --noEmit. exit 0 = types sound.
```

Ready = both exit 0 AND `dist/index.mjs` exists and imports cleanly:

```bash
node -e "import('./dist/index.mjs').then(m => console.log('EXPORTS:', Object.keys(m).join(', ')))"
# EXPECTED: EXPORTS: BodyGraph, renderToSVG
```

Both exit 0 on the 2026-10-26 run (node v22.22.2).

Teardown: nothing to stop. (Scratch SVGs written outside
`skills/verify-hd-bodygraph/evidence/` are removed by `cleanup` — see Cleanup.)

## Doctor

One read-only check answering "is this checkout worth driving?": right repo,
deps installed, buildable, fixture present, export surface intact, CLI usage
path behaving, secret policy intact.

```bash
python3 scripts/control-hd-bodygraph.py doctor
```

JSON on stdout; exit 0 only when every check passes. 2026-10-26 run — **8/8 ok,
exit 0** (saved to `evidence/doctor-normal.json`):

```json
{
  "command": "doctor",
  "ok": true,
  "checks": [
    {"check": "repo-remote", "ok": true, "detail": "origin remote matches expected project"},
    {"check": "node-version", "ok": true, "detail": "node v22.22.2"},
    {"check": "package-identity", "ok": true, "detail": "@gonzih/hd-bodygraph v1.4.1"},
    {"check": "fixture", "ok": true, "detail": "test-chart.json: parses; has definedCenters + channels", "sha256": "1ce0d1f721cd3d90f463699e13041d94acd0fa64d840ba8e4f1c8b269ae34b98"},
    {"check": "npm-build", "ok": true, "detail": "npm run build exit 0"},
    {"check": "lib-exports", "ok": true, "detail": "dist/index.mjs exports: BodyGraph,renderToSVG"},
    {"check": "cli-entry", "ok": true, "detail": "render-cli.mjs present; no-args exit 1 with Usage on stderr"},
    {"check": "env-secret-policy", "ok": true, "detail": "secrets env-only; allowed var(s) set: GITHUB_TOKEN (values never printed or written)"}
  ],
  "failed": []
}
```

Run this first whenever anything looks off.

### Adversarial doctor (proof bar)

Assert origin matches a caller-supplied URL. A wrong URL must fail:

```bash
python3 scripts/control-hd-bodygraph.py doctor \
  --expected-remote https://github.com/wrong/definitely-not-hd-bodygraph.git
```

2026-10-26 run — **exit 1, `"failed": ["expected-remote"]`** (saved to
`evidence/doctor-adversarial.json`). With the *correct* URL the extra check
passes and the run exits 0 again.

## Drive

Harness = the control CLI (real renders through `dist/index.mjs` and
`render-cli.mjs`), or the node one-liners inlined below. Stable handles:
function names (`renderToSVG`), file paths (fixture `reference/test-chart.json`),
theme names (`canonical`), and SVG structure (viewBox attribute, center/gate
markup) — not pixel coordinates.

- **Both render surfaces + manifest (the canonical end-to-end drive):**

  ```bash
  python3 scripts/control-hd-bodygraph.py drive all
  ```

  2026-10-26 run — **exit 0**, per-surface JSON reports (saved to
  `evidence/drive-all.json`):
  - lib: `viewBox "0 0 820 900"`, 35293 bytes,
    sha256 `273ce86f3f67349a92a95ab3a6c1c4fd58bcb35d2d1f0c7afce983989c2bc253`
  - cli: `viewBox "0 0 820 960"`, 24257 bytes,
    sha256 `3f2b7e3c87c45e1798fc004dea2715587c042373afe0720fc633e63699a6fb4f`
  - manifest refreshed (2 entries).

- **Library render only (primary surface):**

  ```bash
  python3 scripts/control-hd-bodygraph.py drive lib
  # EXPECTED: exit 0, viewBox 0 0 820 900 (library geometry)
  ```

- **CLI render only (secondary surface, standalone script path):**

  ```bash
  python3 scripts/control-hd-bodygraph.py drive cli
  # EXPECTED: exit 0, viewBox 0 0 820 960 (render-pro.mjs geometry)
  ```

  Equivalent raw drive:

  ```bash
  node render-cli.mjs reference/test-chart.json canonical \
    > skills/verify-hd-bodygraph/evidence/cli-canonical.svg
  ```

- **Refresh the sha256 manifest (diff hook):**

  ```bash
  python3 scripts/control-hd-bodygraph.py drive manifest
  ```

- **CLI usage-error contract:** no args must exit non-zero with Usage on stderr:

  ```bash
  python3 scripts/control-hd-bodygraph.py drive cli-usage-error
  # 2026-10-26: exit 0 → {"exit_code": 1, "stderr_has_usage": true}
  # (evidence/drive-cli-usage-error.json)
  ```

  Or by hand: `node render-cli.mjs` → exit 1, stderr
  `Usage: node render-cli.mjs <chart.json> [theme]`.

Do NOT drive the library and CLI as if they are the same surface — see the drift
note above. A proof names which entry point it used. An unknown target
(`drive bogus`) exits non-zero with a descriptive error listing valid targets.

## Evidence

Capture under `skills/verify-hd-bodygraph/evidence/` (named location; cleanup must
never delete it). Artifacts after the 2026-10-26 run (all committed):

| file | what it proves |
| --- | --- |
| `lib-canonical.svg` | library render of the fixture (viewBox 0 0 820 900) |
| `cli-canonical.svg` | CLI render of the fixture (viewBox 0 0 820 960) |
| `manifest.sha256` | sha256 per SVG — the diff mechanism: re-run after a change and compare |
| `commands.log` | JSONL of every drive command + stdout/stderr/exit |
| `doctor-normal.json` | normal doctor output (8/8 ok, exit 0) |
| `doctor-adversarial.json` | adversarial doctor output (wrong URL → exit 1) |
| `drive-all.json` | aggregate lib+cli+manifest drive report |
| `drive-cli-usage-error.json` | CLI usage-error contract proof |

Proof standards: exercise the real public path (`renderToSVG` via `dist/`, or
`render-cli.mjs`), never internal helpers; verify the resulting state (SVG bytes,
viewBox, file on disk) not just "no crash"; the fixture `reference/test-chart.json`
is the standing input — a changed fixture invalidates the baseline, record its
sha256 in the manifest (current baseline:
`1ce0d1f721cd3d90f463699e13041d94acd0fa64d840ba8e4f1c8b269ae34b98`).

## Cleanup

Kill what you started; start nothing that lingers. For this surface that means:

```bash
python3 scripts/control-hd-bodygraph.py cleanup
```

- Removes scratch SVGs written to the repo root or `output/` by manual drives
  (`lib-canonical.svg` / `cli-canonical.svg` at root, `output/*-canonical.svg`).
- **Never** deletes `skills/verify-hd-bodygraph/evidence/` — proof artifacts
  survive the teardown by contract.
- No servers, no ports, no data dirs to reclaim.
- Verifies after cleanup: lists every surviving evidence artifact and exits
  non-zero if a required one is missing. A cleanup that eats the proof fails.

2026-10-26 run: planted scratch `lib-canonical.svg` at repo root → cleanup
`exit 0`, `removed_scratch: ["…/lib-canonical.svg"]`, all 8 evidence artifacts
listed as surviving.

## Helpers

- `scripts/control-hd-bodygraph.py` — the control CLI for this skill. Executable,
  JSON on stdout, non-zero exit on any failed check, `--help` exits 0 and
  teaches the whole surface. Secrets from environment only (none required for
  the local surface); values never printed, never written to files.

  ```bash
  python3 scripts/control-hd-bodygraph.py --help            # teaches all subcommands, exit 0
  python3 scripts/control-hd-bodygraph.py doctor            # → JSON, exit 0 when healthy (8/8)
  python3 scripts/control-hd-bodygraph.py doctor --expected-remote <url>  # adversarial mode
  python3 scripts/control-hd-bodygraph.py drive lib         # → library render + evidence
  python3 scripts/control-hd-bodygraph.py drive cli         # → CLI render + evidence
  python3 scripts/control-hd-bodygraph.py drive all         # → lib + cli + manifest
  python3 scripts/control-hd-bodygraph.py drive manifest    # → refresh sha256 manifest
  python3 scripts/control-hd-bodygraph.py drive cli-usage-error  # → usage-error contract
  python3 scripts/control-hd-bodygraph.py cleanup           # → scratch removal + evidence survival check
  ```

Maintenance: keep the feature map and this skill honest as the app changes via
`pstack-maintain-verification-skill`.
