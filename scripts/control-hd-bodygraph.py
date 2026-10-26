#!/usr/bin/env python3
"""Control CLI for the verify-hd-bodygraph skill.

Drives the @gonzih/hd-bodygraph renderer (library + CLI surfaces) the way a
verification run needs to: read-only health checks (`doctor`) and real render
drives (`drive`) that write evidence into the skill's evidence dir.

Surfaces (they are DIFFERENT renderers — name which one you drove):
  lib  — library build: dist/index.mjs  renderToSVG()  (viewBox 0 0 820 900)
  cli  — standalone CLI:  render-cli.mjs → render-pro.mjs (viewBox 0 0 820 960)

All output is JSON on stdout. Diagnostics go to stderr. Exit code is 0 on
success, non-zero on any failed check — safe to gate pipelines on.

Secrets policy: this script reads only the env vars it names in --help.
It never prints secret values, never writes them to files, and never embeds
any credential. (For this local library surface no network secret is needed
at all; the policy is enforced by construction.)

Usage:
  python3 scripts/control-hd-bodygraph.py --help
  python3 scripts/control-hd-bodygraph.py doctor
  python3 scripts/control-hd-bodygraph.py doctor --expected-remote <url>
  python3 scripts/control-hd-bodygraph.py drive lib
  python3 scripts/control-hd-bodygraph.py drive cli
  python3 scripts/control-hd-bodygraph.py drive all
  python3 scripts/control-hd-bodygraph.py drive manifest
  python3 scripts/control-hd-bodygraph.py drive cli-usage-error
  python3 scripts/control-hd-bodygraph.py cleanup
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "skills" / "verify-hd-bodygraph"
EVIDENCE_DIR = SKILL_DIR / "evidence"

FIXTURE = REPO / "reference" / "test-chart.json"
DIST_LIB = REPO / "dist" / "index.mjs"
CLI_SCRIPT = REPO / "render-cli.mjs"

EXPECTED_REMOTE_HOST = "github.com/mbgulden/hd-bodygraph.git"
EXPECTED_PACKAGE_NAME = "@gonzih/hd-bodygraph"
LIB_VIEWBOX = "0 0 820 900"
CLI_VIEWBOX = "0 0 820 960"

# Env vars this script is allowed to consult (policy: env-only, never echoed).
# None of them are required for the local lib/cli surface; they exist so a
# future networked drive can source secrets from the environment without
# changing this script's secret handling.
ALLOWED_ENV_SECRETS = [
    "GITHUB_TOKEN",       # if a drive ever needs to fetch a remote fixture
    "HDE_API_KEY",        # if a drive ever calls the HDE API for a chart
]


class CheckResult:
    def __init__(self, name, ok, detail, extra=None):
        self.name = name
        self.ok = ok
        self.detail = detail
        self.extra = extra or {}

    def to_dict(self):
        d = {"check": self.name, "ok": self.ok, "detail": self.detail}
        d.update(self.extra)
        return d


def run_cmd(cmd, cwd=REPO, timeout=180):
    """Run a command; return (exit_code, stdout, stderr). Never raises on
    non-zero exit — doctor needs to report, not crash."""
    try:
        p = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError as e:
        return 127, "", f"command not found: {e}"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def emit(payload, ok):
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    sys.exit(0 if ok else 1)


# ---------------------------------------------------------------- doctor ----

def doctor(expected_remote=None):
    """Read-only battery answering 'is this checkout worth driving?'."""
    checks = []

    # 1. Repo remote matches the project we are verifying.
    rc, out, _ = run_cmd(["git", "remote", "get-url", "origin"])
    remote = out.strip()
    ok = rc == 0 and EXPECTED_REMOTE_HOST in remote
    # Strip any embedded credential before it can reach the report.
    redacted = re.sub(r"://[^@/]+@", "://***@", remote) if remote else ""
    checks.append(CheckResult(
        "repo-remote", ok,
        "origin remote matches expected project" if ok
        else "origin remote missing or does not match " + EXPECTED_REMOTE_HOST,
        {"remote": redacted},
    ))

    # 2. Node available and version recorded.
    rc, out, _ = run_cmd(["node", "--version"])
    node_ver = out.strip()
    checks.append(CheckResult(
        "node-version", rc == 0 and bool(node_ver),
        f"node {node_ver}" if rc == 0 else "node not found or failed to report version",
    ))

    # 3. Package identity (name + version) from package.json.
    try:
        pkg = json.loads((REPO / "package.json").read_text())
        name, ver = pkg.get("name"), pkg.get("version")
        ok = name == EXPECTED_PACKAGE_NAME
        checks.append(CheckResult(
            "package-identity", ok,
            f"{name} v{ver}" + ("" if ok else f" (expected {EXPECTED_PACKAGE_NAME})"),
        ))
    except Exception as e:
        checks.append(CheckResult("package-identity", False, f"package.json unreadable: {e}"))

    # 4. Fixture parses as JSON and has the fields a chart needs.
    try:
        chart = json.loads(FIXTURE.read_text())
        missing = [k for k in ["definedCenters", "channels"] if k not in chart]
        ok = not missing
        checks.append(CheckResult(
            "fixture", ok,
            f"{FIXTURE.name}: " + (
                "parses; has definedCenters + channels" if ok
                else "missing fields: " + ", ".join(missing)),
            {"sha256": sha256_file(FIXTURE)},
        ))
    except Exception as e:
        checks.append(CheckResult("fixture", False, f"fixture unreadable/unparsable: {e}"))

    # 5. Build is current: npm run build exits 0.
    rc, _, err = run_cmd(["npm", "run", "build"], timeout=300)
    checks.append(CheckResult(
        "npm-build", rc == 0,
        "npm run build exit 0" if rc == 0 else f"npm run build failed (exit {rc}): {err.strip()[:200]}",
    ))

    # 6. Library dist exposes the public API.
    lib_probe = (
        "import('./dist/index.mjs').then(m => { const e=Object.keys(m);"
        " if(!e.includes('renderToSVG')||!e.includes('BodyGraph'))"
        " { console.error('MISSING'); process.exit(1); }"
        " console.log(e.join(',')) })"
    )
    rc, out, err = run_cmd(["node", "-e", lib_probe])
    exports = out.strip()
    ok = rc == 0 and "renderToSVG" in exports and "BodyGraph" in exports
    checks.append(CheckResult(
        "lib-exports", ok,
        f"dist/index.mjs exports: {exports}" if ok
        else f"dist/index.mjs import failed or exports incomplete (exit {rc}): {err.strip()[:200]}",
    ))

    # 7. CLI entry exists and its usage-error path behaves (exit 1 + Usage line).
    ok_cli = CLI_SCRIPT.exists()
    if ok_cli:
        rc, _, err = run_cmd(["node", "render-cli.mjs"])
        ok_cli = rc != 0 and "Usage" in err
        detail = (f"render-cli.mjs present; no-args exit {rc} with Usage on stderr")
    else:
        detail = "render-cli.mjs missing"
    checks.append(CheckResult("cli-entry", ok_cli, detail))

    # 8. Adversarial hook: caller-supplied expected remote (proof-bar use).
    if expected_remote:
        ok = expected_remote in (remote or "")
        checks.append(CheckResult(
            "expected-remote", ok,
            f"origin matches --expected-remote={redact(expected_remote)}"
            if ok else "origin does NOT match --expected-remote (adversarial check failed as intended or misconfigured)",
        ))

    # 9. Env secret policy: confirm we would never surface a secret.
    present = [v for v in ALLOWED_ENV_SECRETS if os.environ.get(v)]
    checks.append(CheckResult(
        "env-secret-policy", True,
        "secrets env-only; " + (
            "allowed var(s) set: " + ", ".join(present) + " (values never printed or written)"
            if present else "no allowed secret vars set (not required for local surface)"),
    ))

    failed = [c for c in checks if not c.ok]
    emit(
        {
            "command": "doctor",
            "ok": not failed,
            "checks": [c.to_dict() for c in checks],
            "failed": [c.name for c in failed],
        },
        ok=not failed,
    )


def redact(url):
    return re.sub(r"://[^@/]+@", "://***@", url)


# ----------------------------------------------------------------- drive ----

def ensure_evidence_dir():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def log_command(cmd, rc, out, err, path):
    """Append command+outputs to commands.log (no secrets in these cmds)."""
    with open(path, "a") as f:
        f.write(json.dumps({
            "cmd": cmd, "exit": rc,
            "stdout": out.strip()[:2000], "stderr": err.strip()[:2000],
        }, ensure_ascii=False) + "\n")


def drive_lib():
    """Render the fixture through the library build → evidence/lib-canonical.svg."""
    ensure_evidence_dir()
    target = EVIDENCE_DIR / "lib-canonical.svg"
    prog = """
import fs from 'fs';
const m = await import('./dist/index.mjs');
const chart = JSON.parse(fs.readFileSync('reference/test-chart.json','utf8'));
const svg = m.renderToSVG(chart, {theme:'canonical'});
fs.writeFileSync(process.argv[1], svg);
const vb = (svg.match(/viewBox="([^"]+)"/)||[])[1];
console.log(JSON.stringify({viewBox: vb, bytes: svg.length}));
"""
    cmd = ["node", "--input-type=module", "-e", prog, str(target)]
    rc, out, err = run_cmd(cmd)
    log_command(cmd, rc, out, err, EVIDENCE_DIR / "commands.log")
    if rc != 0:
        emit({"command": "drive lib", "ok": False,
              "error": f"library render failed (exit {rc}): {err.strip()[:500]}"}, ok=False)
    info = None
    try:
        info = json.loads(out.strip().splitlines()[-1])
    except Exception:
        emit({"command": "drive lib", "ok": False,
              "error": f"render produced no parseable output: {out.strip()[:200]} / {err.strip()[:300]}"}, ok=False)
    if not target.exists():
        emit({"command": "drive lib", "ok": False,
              "error": f"render reported success but {target} was not written"}, ok=False)
    assert info is not None  # unreachable here: except path exits
    vb_ok = info.get("viewBox") == LIB_VIEWBOX
    ok = vb_ok
    emit({
        "command": "drive lib", "ok": ok,
        "surface": "library (dist/index.mjs renderToSVG)",
        "svg": str(target),
        "viewBox": info.get("viewBox"),
        "viewBox_expected": LIB_VIEWBOX,
        "bytes": info.get("bytes"),
        "sha256": sha256_file(target),
        "error": None if ok else f"unexpected viewBox {info.get('viewBox')!r}, expected {LIB_VIEWBOX!r}",
    }, ok=ok)


def drive_cli():
    """Render the fixture through the standalone CLI → evidence/cli-canonical.svg."""
    ensure_evidence_dir()
    target = EVIDENCE_DIR / "cli-canonical.svg"
    rc, out, err = run_cmd(["node", "render-cli.mjs", "reference/test-chart.json", "canonical"])
    if rc != 0:
        log_command(["node", "render-cli.mjs", "reference/test-chart.json", "canonical"],
                    rc, out, err, EVIDENCE_DIR / "commands.log")
        emit({"command": "drive cli", "ok": False,
              "error": f"CLI render failed (exit {rc}): {err.strip()[:500]}"}, ok=False)
    target.write_text(out)
    sha = hashlib.sha256(out.encode()).hexdigest()
    vb = (re.search(r'viewBox="([^"]+)"', out) or [None, None])[1]
    vb_ok = vb == CLI_VIEWBOX
    log_command(["node", "render-cli.mjs", "reference/test-chart.json", "canonical"],
                rc, out[:200], err, EVIDENCE_DIR / "commands.log")
    ok = vb_ok and out.startswith("<svg")
    emit({
        "command": "drive cli", "ok": ok,
        "surface": "CLI (render-cli.mjs → render-pro.mjs)",
        "svg": str(target),
        "viewBox": vb,
        "viewBox_expected": CLI_VIEWBOX,
        "bytes": len(out),
        "sha256": sha,
        "error": None if ok else f"unexpected viewBox {vb!r}, expected {CLI_VIEWBOX!r}",
    }, ok=ok)


def drive_manifest():
    """Write/refresh the sha256 manifest for every evidence SVG (diff hook)."""
    ensure_evidence_dir()
    manifest = {}
    for svg in sorted(EVIDENCE_DIR.glob("*.svg")):
        manifest[svg.name] = sha256_file(svg)
    manifest_path = EVIDENCE_DIR / "manifest.sha256"
    manifest_path.write_text(
        "\n".join(f"{h}  {n}" for n, h in sorted(manifest.items())) + "\n"
    )
    emit({"command": "drive manifest", "ok": True,
          "manifest": str(manifest_path), "entries": manifest}, ok=True)


def drive_cli_usage_error():
    """Prove the CLI's usage-error contract: no args → exit 1 + Usage on stderr."""
    rc, out, err = run_cmd(["node", "render-cli.mjs"])
    ok = rc != 0 and "Usage" in err
    emit({
        "command": "drive cli-usage-error", "ok": ok,
        "surface": "CLI (render-cli.mjs)",
        "exit_code": rc, "stderr_has_usage": "Usage" in err,
        "error": None if ok else f"expected non-zero exit + Usage on stderr, got exit {rc}, stderr {err.strip()[:200]!r}",
    }, ok=ok)


def cleanup():
    """Remove scratch state from this run WITHOUT touching the evidence dir.

    Scope (this surface has no servers, ports, or data dirs to reclaim):
      - scratch SVGs written to the repo root or output/ by manual drives
        (anything outside skills/verify-hd-bodygraph/evidence/);
      - nothing else. The evidence dir is proof — it is never deleted here.
    Verifies afterwards that every evidence artifact still exists, and fails
    (exit 1) if a prior cleanup step is found to have eaten the proof.
    """
    removed = []
    for name in ("lib-canonical.svg", "cli-canonical.svg"):
        root_scratch = REPO / name
        if root_scratch.exists():
            root_scratch.unlink()
            removed.append(str(root_scratch))
    out_dir = REPO / "output"
    if out_dir.is_dir():
        for svg in sorted(out_dir.glob("*-canonical.svg")):
            svg.unlink()
            removed.append(str(svg))
    artifacts = [f.name for f in sorted(EVIDENCE_DIR.iterdir())
                 if f.is_file()] if EVIDENCE_DIR.is_dir() else []
    required = ["lib-canonical.svg", "cli-canonical.svg",
                "manifest.sha256", "commands.log"]
    missing = [n for n in required if n not in artifacts]
    ok = not missing
    emit({
        "command": "cleanup",
        "ok": ok,
        "removed_scratch": removed,
        "evidence_dir": str(EVIDENCE_DIR),
        "evidence_artifacts": artifacts,
        "error": None if ok
                else "evidence artifacts missing after cleanup: " + ", ".join(missing),
    }, ok=ok)


def drive(target):
    if target == "lib":
        drive_lib()
    elif target == "cli":
        drive_cli()
    elif target == "manifest":
        drive_manifest()
    elif target == "cli-usage-error":
        drive_cli_usage_error()
    elif target == "all":
        # Drive lib + cli + manifest as child invocations so each emits its
        # own report; keep going after a failure so the aggregate shows both
        # surfaces. Exit non-zero if lib or cli failed.
        results = {}
        for t in ("lib", "cli", "manifest"):
            rc, out, err = run_cmd(
                [sys.executable, str(Path(__file__).resolve()), "drive", t])
            results[t] = {"exit": rc, "output": out.strip()}
        ok = results["lib"]["exit"] == 0 and results["cli"]["exit"] == 0
        emit({"command": "drive all", "ok": ok, "results": results}, ok=ok)
    else:
        emit({"command": f"drive {target}", "ok": False,
              "error": f"unknown drive target {target!r}; valid: lib, cli, all, manifest, cli-usage-error"},
             ok=False)


# ----------------------------------------------------------------- main ----

def main():
    p = argparse.ArgumentParser(
        prog="control-hd-bodygraph.py",
        description=(
            "Control CLI for the verify-hd-bodygraph skill: read-only doctor "
            "checks and real render drives for the @gonzih/hd-bodygraph "
            "library (viewBox 0 0 820 900) and standalone CLI "
            "(viewBox 0 0 820 960) surfaces. JSON output; non-zero exit on "
            "failure. Secrets come from environment variables only "
            "(none required for the local surface) and are never printed "
            "or written to files."),
        epilog=(
            "Examples:\n"
            "  python3 scripts/control-hd-bodygraph.py doctor\n"
            "  python3 scripts/control-hd-bodygraph.py doctor --expected-remote https://github.com/mbgulden/hd-bodygraph.git\n"
            "  python3 scripts/control-hd-bodygraph.py drive lib\n"
            "  python3 scripts/control-hd-bodygraph.py drive cli\n"
            "  python3 scripts/control-hd-bodygraph.py drive all\n"
            "  python3 scripts/control-hd-bodygraph.py drive manifest\n"
            "  python3 scripts/control-hd-bodygraph.py drive cli-usage-error\n"
            "  python3 scripts/control-hd-bodygraph.py cleanup\n"
            "Evidence lands in skills/verify-hd-bodygraph/evidence/ "
            "(SVGs + manifest.sha256 + commands.log)."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser(
        "doctor",
        help="read-only health battery (JSON, exit 0 only when all checks pass)",
        description=(
            "Check: repo remote, node version, package name/version, fixture "
            "parses, npm build exit 0, dist exports renderToSVG+BodyGraph, "
            "CLI usage-error path, env secret policy. With --expected-remote, "
            "additionally assert origin matches that exact URL (adversarial "
            "mode for the proof bar)."),
    )
    d.add_argument(
        "--expected-remote",
        help="assert origin remote contains this exact string; failure exits non-zero (adversarial use).",
    )

    dr = sub.add_parser(
        "drive",
        help="exercise a render surface end-to-end and save evidence",
        description=(
            "Targets: lib = library renderToSVG via dist/ (viewBox 0 0 820 900); "
            "cli = render-cli.mjs standalone renderer (viewBox 0 0 820 960); "
            "all = lib + cli + manifest; manifest = refresh sha256 manifest; "
            "cli-usage-error = prove no-args exits non-zero with Usage. "
            "Each target writes/refreshes artifacts under "
            "skills/verify-hd-bodygraph/evidence/ and prints a JSON report."),
    )
    dr.add_argument("target", choices=["lib", "cli", "all", "manifest", "cli-usage-error"])

    sub.add_parser(
        "cleanup",
        help="remove scratch state (never the evidence dir) and verify evidence survives",
        description=(
            "Remove scratch SVGs written to the repo root or output/ by "
            "manual drives. Never touches skills/verify-hd-bodygraph/evidence/ "
            "(proof artifacts survive teardown by contract). Afterwards lists "
            "the surviving evidence artifacts and exits non-zero if any "
            "required artifact is missing."
        ),
    )

    args = p.parse_args()
    if args.command == "doctor":
        doctor(expected_remote=args.expected_remote)
    elif args.command == "drive":
        drive(args.target)
    elif args.command == "cleanup":
        cleanup()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # descriptive-error guarantee
        json.dump({"command": "<unhandled>", "ok": False,
                   "error": f"{type(e).__name__}: {e}"}, sys.stdout)
        sys.stdout.write("\n")
        sys.exit(1)
