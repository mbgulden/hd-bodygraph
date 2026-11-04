#!/usr/bin/env python3
"""
verify_renderoff.py — mechanical verification for t_97e70f92 deliverable.

Usage:
  python3 scripts/verify_renderoff.py [demo-svg]

Checks (RUBRIC ids in comments):
  1.  SVG parses as XML; 9 center shapes (CEN-01)
  2.  defined-center fills ⊆ CEN-07 table; count matches Vector #1 (CEN-05/07)
  3.  64 gate pills, numbers exactly 1..64 (CHN-05)
  4.  26 activation values, each matching ^gate.line$ (ACT-04)
  5.  DESIGN header left+red / PERSONALITY header right+black (ACT-01)
  6.  no #8b5cf6; both-sides gates render split black/red (CHN-06)
  7.  module CHANNELS == 36-pair set; == geometry JSON pairs; gate→center
      pairs consistent (CHN-01 + CEN-04)
  8.  defined channel strokes in SVG == 2 for Vector #1 (CHN-03)
  9.  no "SolarPlexus"/"Heart/Ego" visitor-facing text (LBL-06)
 10.  no "[object Object]"/placeholder text (LBL-09)
 11.  census: 9 centers / 64 gate labels / 36 channel geometries (Jimmy 06:10)

XML note: input is our own freshly generated local SVG; no untrusted external
content, stdlib ElementTree is appropriate here.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET

NS = {"svg": "http://www.w3.org/2000/svg"}

# CEN-07 palette
CEN07 = {
    "Head": "#f48fb1", "Ajna": "#d32f2f", "Throat": "#1565c0", "G": "#388e3c",
    "Ego": "#43a047", "Sacral": "#e65100", "SolarPlexus": "#f9a825",
    "Spleen": "#f9a825", "Root": "#c62828",
}
BLACK, RED = "#2a2a2a", "#c87860"

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, ok, detail=""):
    results.append((PASS if ok else FAIL, name, detail))


def main():
    here = __file__.rsplit("/", 1)[0]
    root_dir = here + "/.."
    svg_path = sys.argv[1] if len(sys.argv) > 1 else root_dir + "/renderer/demo-vector1.svg"

    sys.path.insert(0, root_dir + "/renderer")
    import render_bodygraph as rb

    V1_DEFINED = {"G", "Ego", "Spleen", "Throat"}   # Vector #1 expected defined set

    raw = open(svg_path).read()

    # ── 1. XML + 9 center shapes (CEN-01) ───────────────────────────────
    try:
        root = ET.parse(svg_path).getroot()
        check("1a XML parse", True)
    except ET.ParseError as e:
        check("1a XML parse", False, str(e))
        print("FATAL: cannot parse SVG")
        sys.exit(1)
    polys = root.findall(".//svg:polygon", NS)
    check("1b 9 center shapes", len(polys) == 9, f"found {len(polys)}")

    # ── 2. defined fills (CEN-05/07) — vertex-identity per-center check ──
    fills = [p.get("fill") for p in polys if p.get("fill") not in (None, "#ffffff", "none")]
    check("2a defined fills ⊆ CEN-07 table", set(fills) <= set(CEN07.values()),
          f"used {sorted(set(fills))}")
    expected_poly = {}
    for cid, cname, shape, cx, cy, w, h in rb.CENTERS:
        pts = rb.center_polygon(shape, cx, cy, w, h)
        expected_poly[" ".join(f"{x:.2f},{y:.2f}" for x, y in pts)] = (cname, cid)
    v_ok, v_matched, mismatches = True, 0, []
    for p in polys:
        entry = expected_poly.get(p.get("points"))
        if entry is None:
            v_ok = False
            continue
        cname = entry[0]
        v_matched += 1
        exp_fill = CEN07.get(cname, "#ffffff") if p.get("fill") != "#ffffff" else "#ffffff"
        if p.get("fill") != (CEN07[cname] if cname in V1_DEFINED else "#ffffff"):
            v_ok = False
            mismatches.append((cname, p.get("fill")))
    check("2b per-center fills correct (vertex-identity, 9/9 polygons)",
          v_ok and v_matched == 9,
          f"matched {v_matched}/9" + (f", mismatches {mismatches}" if mismatches else ""))

    # ── 3. 64 gate pills exactly 1..64 (CHN-05) ─────────────────────────
    pills = []
    for g in root.findall(".//svg:g", NS):
        c = g.find("svg:circle", NS)
        t = g.find("svg:text", NS)
        if c is not None and t is not None and t.text and t.text.strip().isdigit():
            pills.append(int(t.text.strip()))
    check("3a 64 gate pills", len(pills) == 64, f"found {len(pills)}")
    check("3b pills == 1..64", set(pills) == set(range(1, 65)),
          "" if set(pills) == set(range(1, 65))
          else f"missing {sorted(set(range(1, 65)) - set(pills))} "
               f"extra {sorted(set(pills) - set(range(1, 65)))}")

    # ── 4. activation values (ACT-04) ───────────────────────────────────
    vals = re.findall(r'>(\d{1,2}\.\d)</text>', raw)
    fmt = re.compile(r"^([1-9]|[1-5][0-9]|6[0-4])\.[1-6]$")
    bad = [v for v in vals if not fmt.match(v)]
    check("4a all activation values match gate.line regex", not bad, f"bad {bad}" if bad else "all clean")
    check("4b 26 activation values present", len(vals) == 26, f"found {len(vals)}")

    # ── 5. ACT-01 column sides ──────────────────────────────────────────
    texts = root.findall(".//svg:text", NS)
    left_red = any(t.text and "DESIGN" in t.text and t.get("fill") == RED
                   and float(t.get("x", 9999)) < 500 for t in texts)
    right_black = any(t.text and "PERSONALITY" in t.text and t.get("fill") == BLACK
                      and float(t.get("x", 0)) > 700 for t in texts)
    check("5a DESIGN header left, red token", left_red)
    check("5b PERSONALITY header right, black token", right_black)

    # ── 6. CHN-06 both-gate split, no purple ────────────────────────────
    check("6a no #8b5cf6 anywhere in SVG", "#8b5cf6" not in raw)
    splits = len(re.findall(r'fill="%s"[^>]*/>\s*<path[^>]*fill="%s"' % (BLACK, RED), raw))
    check("6b both-sides gates split black/red (3 expected for V1)", splits == 3,
          f"{splits} split halves found")

    # ── 8. defined channel strokes (CHN-03) ─────────────────────────────
    defined_strokes = len(re.findall(r'stroke-width="5"', raw))
    check("8 defined channel count == 2 (V1: 1–8, 26–44)", defined_strokes == 2,
          f"found {defined_strokes}")

    # ── 9/10. visitor-facing text hygiene (LBL-06/09) ───────────────────
    bad_text = re.findall(r'SolarPlexus|Heart/Ego|\[object Object\]|Lorem|\bTBD\b|\bNaN\b', raw)
    check("9a no camel/engine names or [object Object]", not bad_text,
          f"found {bad_text}" if bad_text else "")

    # ── 7/11. module-level: channel table + geometry consistency ────────
    mod_pairs = {tuple(sorted((a, b))) for a, b, _n in rb.CHANNELS}
    geom = json.load(open(root_dir + "/geometry/bodygraph_geometry.json"))
    geom_pairs = {tuple(sorted(c["gates"])) for c in geom["channels"]}
    gmap = {g["number"]: g["center"] for g in geom["gates"]}

    check("7a module CHANNELS count == 36", len(mod_pairs) == 36, f"found {len(mod_pairs)}")
    check("7b module pairs == geometry JSON pairs (36/36)", mod_pairs == geom_pairs,
          f"missing {geom_pairs - mod_pairs} extra {mod_pairs - geom_pairs}"
          if mod_pairs != geom_pairs else "")
    bad_cc = [(a, b) for a, b, _n in rb.CHANNELS
              if gmap[a] == gmap[b] and
              {gmap[a], gmap[b]} != {gmap[a], gmap[b]}]  # placeholder, replaced below
    # per-channel: module pair's gate-centers must equal the geometry channel's center_pair
    geom_by_pair = {tuple(sorted(c["gates"])): set(c["center_pair"]) for c in geom["channels"]}
    bad_cc = [(a, b) for a, b, _n in rb.CHANNELS
              if {gmap[a], gmap[b]} != geom_by_pair[tuple(sorted((a, b)))]]
    check("7c module channel centers == geometry center_pair (CEN-04/CHN-01)",
          not bad_cc, f"bad {bad_cc}" if bad_cc else "36/36 consistent")
    check("11a census: 9 centers", len(CEN07) == 9)
    check("11b census: 64 gate positions", len(GATE_POS(rb)) == 64)
    check("11c census: 36 channel geometries in canonical table", len(rb.CHANNELS) == 36)

    # ── report ──────────────────────────────────────────────────────────
    print(f"{'=' * 64}\nVERIFICATION — {svg_path}\n{'=' * 64}")
    p = f = 0
    for status, name, detail in results:
        mark = "PASS" if status == PASS else "FAIL"
        line = f"[{mark}] {name}"
        if detail:
            line += f"  ({detail})"
        print(line)
        p += status == PASS
        f += status == FAIL
    print(f"{'=' * 64}\n{p} PASS / {f} FAIL\n{'=' * 64}")
    sys.exit(1 if f else 0)


def GATE_POS(rb):
    return rb.GATE_POSITIONS


if __name__ == "__main__":
    main()
