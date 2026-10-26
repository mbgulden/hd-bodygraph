# Acceptance Report — verify-hd-bodygraph (t_95e12adc)

Date: 2026-10-26 (MDT/UTC as noted; battery at 2026-10-26T13:17Z) — final acceptance check, run LIVE by the acceptance worker
(not from the parent's self-report; every claim below was re-executed or re-read against the commit).
Method per task comment: pstack-interrogate framing — verdict below is FIRST-PASS (fleet note:
settles only after jimmy second-witnesses in the kanban review step).

## 1. Confirmed live repo

| Fact | Value | How confirmed |
|---|---|---|
| Remote | https://github.com/mbgulden/hd-bodygraph.git | `git remote get-url origin` (exit 0) |
| Branch | muse/verify-hd-bodygraph | `git branch --show-current` |
| HEAD | 6bfce068cc5a824b114fafcb9d74c4ade25aabc3 | `git rev-parse HEAD`; subject "feat: verify-hd-bodygraph skill — control CLI, feature map, proof-bar evidence" |
| Pushed? | NO | `git ls-remote --heads origin muse/verify-hd-bodygraph` → empty |
| Surface | library + CLI, on-demand (no daemon) | `systemctl list-units --all \| grep -i bodygraph` → no unit (matches t_b6f3ce66: HDE services live in a different checkout, hd-platform) |
| Node / package | node v22.22.2, @gonzih/hd-bodygraph v1.4.1 | doctor output (fresh run) |

## 2. Acceptance criteria (all re-verified fresh)

| # | Criterion | Result |
|---|---|---|
| 1 | All specified files exist (disk AND in commit 6bfce06) | PASS — 25/25 checked via `git cat-file -e HEAD:<path>` + `[ -f ]`, 0 missing |
| 2 | Feature index count == feature files on disk | PASS — README links 14 == 14 .md feature files; link set set-equal to disk set; all 14 files pass four-H2 shape check |
| 3 | Both doctor outputs quoted in report | PASS — quoted in full in §4 (fresh runs) |
| 4 | Evidence paths correctly named | PASS — all 8 named evidence files exist in skills/verify-hd-bodygraph/evidence/ (disk + commit); manifest sha256s recompute MATCH |
| 5 | No secret values in committed files (grep) | PASS — 0 hits, methodology §6 |

## 3. Files created (25, committed on muse/verify-hd-bodygraph @ 6bfce06)

- Skill: skills/verify-hd-bodygraph/SKILL.md (six sections, 0 placeholders — `grep -nE 'TODO|PLACEHOLDER|<fill|FIXME|\[TBD\]'` → none)
- Control CLI: scripts/control-hd-bodygraph.py (doctor + drive lib/cli/all/manifest/cli-usage-error + cleanup; JSON output; env-only secrets)
- Feature map: features/README.md (index) + 14 feature files (render-to-svg, bodygraph-react, render-cli, render-hde, test-render, build-typecheck, screenshot-png, pixeldiff, render-png, vision-compare, compare, refine-loop, apply-fixes, diff-structures) — 15 .md total under features/
- Evidence (8): evidence/{lib-canonical.svg, cli-canonical.svg, manifest.sha256, commands.log, doctor-normal.json, doctor-adversarial.json, drive-all.json, drive-cli-usage-error.json}

Scope-clean note: pre-existing working-tree modifications (package-lock.json, render-cli.mjs, scripts/refine-loop.sh) and untracked scratch files (scratch-*, find_*, render-pro.mjs, render-hde.mjs, reference.jpg) were NOT swept into the commit — confirmed by `git status --porcelain` at T0.

## 4. Both doctor outputs (fresh runs this acceptance pass)

### 4.1 doctor (normal) — EXIT 0, 8/8 ok

```json
{
  "command": "doctor",
  "ok": true,
  "checks": [
    {"check": "repo-remote", "ok": true, "detail": "origin remote matches expected project", "remote": "https://github.com/mbgulden/hd-bodygraph.git"},
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

### 4.2 doctor --expected-remote https://github.com/wrong-org/hd-bodygraph (adversarial) — EXIT 1

```json
{
  "command": "doctor",
  "ok": false,
  "checks": [
    {"check": "repo-remote", "ok": true, "detail": "origin remote matches expected project", "remote": "https://github.com/mbgulden/hd-bodygraph.git"},
    {"check": "node-version", "ok": true, "detail": "node v22.22.2"},
    {"check": "package-identity", "ok": true, "detail": "@gonzih/hd-bodygraph v1.4.1"},
    {"check": "fixture", "ok": true, "detail": "test-chart.json: parses; has definedCenters + channels", "sha256": "1ce0d1f721cd3d90f463699e13041d94acd0fa64d840ba8e4f1c8b269ae34b98"},
    {"check": "npm-build", "ok": true, "detail": "npm run build exit 0"},
    {"check": "lib-exports", "ok": true, "detail": "dist/index.mjs exports: BodyGraph,renderToSVG"},
    {"check": "cli-entry", "ok": true, "detail": "render-cli.mjs present; no-args exit 1 with Usage on stderr"},
    {"check": "expected-remote", "ok": false, "detail": "origin does NOT match --expected-remote (adversarial check failed as intended or misconfigured)"},
    {"check": "env-secret-policy", "ok": true, "detail": "secrets env-only; allowed var(s) set: GITHUB_TOKEN (values never printed or written)"}
  ],
  "failed": ["expected-remote"]
}
```

The committed evidence/doctor-normal.json and evidence/doctor-adversarial.json (as committed) show the identical check sets and outcomes (9 checks; failed=[expected-remote]); the only textual difference vs the fresh runs is cosmetic: the committed runs redacted remote string ("https://***@github.com/…") — see Drift D3.

## 5. Evidence paths (named and verified)

All under skills/verify-hd-bodygraph/evidence/ (disk mtime + commit presence confirmed):

| File | Verified |
|---|---|
| lib-canonical.svg (35345 B) | sha256 273ce86f3f67349a92a95ab3a6c1c4fd58bcb35d2d1f0c7afce983989c2bc253 — recomputed, MATCH manifest |
| cli-canonical.svg (24258 B) | sha256 3f2b7e3c87c45e1798fc004dea2715587c042373afe0720fc633e63699a6fb4f — recomputed, MATCH manifest |
| manifest.sha256 | 2 entries, both recompute-match |
| commands.log | present (disk has 1 extra appended re-run line vs commit — Drift D2) |
| doctor-normal.json | ok=true, failed=[] (quoted §4.1) |
| doctor-adversarial.json | ok=false, failed=["expected-remote"] (quoted §4.2) |
| drive-all.json | lib exit 0 viewBox "0 0 820 900"; cli exit 0 viewBox "0 0 820 960"; manifest exit 0 |
| drive-cli-usage-error.json | exit_code 1, stderr_has_usage true |

## 6. Secret scan (methodology + result)

Scope: ALL 66 files in commit 6bfce06 (`git ls-tree -r HEAD`), read via `git cat-file -p` (committed content, not disk).
Patterns: the live $GITHUB_TOKEN value (set in this env, never printed) + `ghp_/gho_/ghu_[A-Za-z0-9]{36}`, `sk-ant-[A-Za-z0-9-]{16,}`, `xox[baprs]-…`, `AKIA[0-9A-Z]{16}`.
Binary coverage: output/current.png (the only binary in the commit) got a strict byte-level grep — 0 matches.
RESULT: 0 hits across all committed files. PASS.

## 7. Commands executed (fresh acceptance battery, 2026-10-26T13:17Z)

| Command | Exit |
|---|---|
| `python3 scripts/control-hd-bodygraph.py doctor` | 0 |
| `python3 scripts/control-hd-bodygraph.py doctor --expected-remote https://github.com/wrong-org/hd-bodygraph` | 1 (intended) |
| `python3 scripts/control-hd-bodygraph.py doctor --help` | 0 |
| feature index/disk count script (README links vs glob) | 0 — 14==14, set-equal, four-H2 PASS |
| 25-file existence check (disk + `git cat-file -e HEAD:<f>`) | 0 — 0 missing |
| `ls -la skills/verify-hd-bodygraph/evidence/` | 0 — 8/8 named files |
| `git diff --stat HEAD -- skills/verify-hd-bodygraph/` | 0 — 1 file +1 line (commands.log) |
| secret scan loop over all committed blobs | 0 hits |
| `git ls-remote --heads origin muse/verify-hd-bodygraph` | 0 — empty (not pushed) |
| `git rev-parse HEAD` / `git branch --show-current` / `git log -1` | 0 — 6bfce06… / muse/verify-hd-bodygraph |
| `systemctl list-units --all \| grep -i bodygraph` | 1 (no match) — on-demand surface, expected |
| `sha256sum` recompute vs manifest.sha256 | 0 — 2/2 MATCH |
| SKILL.md placeholder grep | 0 (no matches) |

## 8. Drift between feature map and application reality

D1. **Two renderers, two viewBoxes** (documented, not a defect): library dist renderToSVG → viewBox 0 0 820 900 (35293 bytes, deterministic — sha re-verified); render-cli.mjs → standalone render-pro.mjs → viewBox 0 0 820 960 (24257 bytes). Feature map flags this in features/render-cli.md as a gotcha and the control CLI encodes per-surface expectations.

D2. **evidence/commands.log: disk vs commit** — disk has exactly ONE appended line (a re-run of the lib render entry, same deterministic result: exit 0, viewBox 820x900, 35293 bytes, sha 273ce86f unchanged). The SVG evidence on disk is byte-identical to the committed version (manifest recompute MATCH). Cosmetic append-only-log drift; not swept into a new commit by this acceptance pass.

D3. **Remote credential redaction (historical, resolved)** — the control script redacts userinfo only when present (`re.sub(r"://[^@/]+@", "://***@", …)`, scripts/control-hd-bodygraph.py:116); the committed doctor JSONs contain "https://***@github.com/…", which proves the parent's run saw a credential-bearing origin URL at that moment. At acceptance time the origin URL has no userinfo component (grep count 0), i.e. it is clean now. The script's redaction plus the §6 scan (0 hits incl. the token value itself) confirm no secret leaked into committed files.

D4. **Unreachable features, honestly labeled** (from feature-map run, re-confirmed live): screenshot/render-png/refine-loop need Playwright+Puppeteer browser binaries (not installed); compare/vision-compare need ANTHROPIC_API_KEY (not set); react-dom not installed so BodyGraph is verified headless only (element object + inner HTML). All documented in the feature files with exact errors — no mock/no-op data presented as live truth.

D5. **No daemon** — hd-bodygraph is on-demand (library/CLI); nothing serves it; no systemd unit. Consistent with the brief's "library/CLI" surface classification.

## 9. Interrogate verdict (FIRST-PASS — settles after jimmy second-witness)

Intent: accept the verify-hd-bodygraph deliverable — prove the 25 committed files exist and are consistent, the control CLI's doctor behaves correctly in normal + adversarial mode, evidence is intact and correctly named, and no secrets leaked into the commit.

Act on: none. No correctness/security/maintainability defect found in the committed set.
Consider: none blocking; D2 (commands.log +1 line on disk) could be re-committed in a future housekeeping pass if the branch is ever pushed — not required for acceptance.
Noted: D1 viewBox drift (documented by design), D3 remote redaction history (improved since; nothing to fix), D4 unreachable features (environment-dependent, documented).
Dismissed: nothing to dismiss — no reviewer-level disagreement was possible in a single-worker pass; the adversarial angle (parent self-report vs fresh re-execution) found no overclaim.

## 10. Boundary — NOT claiming

- NOT claiming the branch is pushed or published (it is local only; push needs explicit authorization).
- NOT claiming a canonical full-suite green: this is an ad-hoc targeted acceptance pass over the skill's own proof bar (doctor + drive + evidence + secret scan), re-executed live; it does not run the project's broader test suite.
- NOT claiming the review verdict is final: first-pass per pstack-interrogate fleet note; jimmy second-witnesses at the kanban review step.
- NOT claiming the pre-existing dirty files (package-lock.json, render-cli.mjs, scripts/refine-loop.sh + untracked scratch) belong to this deliverable — they were correctly excluded.

STATUS: PASS (card scope).
