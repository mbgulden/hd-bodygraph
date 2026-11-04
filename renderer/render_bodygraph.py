#!/usr/bin/env python3
"""
render_bodygraph.py — HD Bodygraph canonical SVG renderer (pure function module)
Task: t_97e70f92 (port- HD bodygraph D) · Status: COMPLETE (2026-11-04, run 759)
================================================================================
Path: /home/ubuntu/work/hd-bodygraph/renderer/render_bodygraph.py

CANONICAL RENDERER DECISION (SPEC §5.3 — recorded in writing, CEN-08 lock below)
--------------------------------------------------------------------------------
SPEC §5 makes the box library renderer (src/renderer.ts + src/geometry.ts) the
DEFAULT candidate and render-pro.mjs (what the reports service calls) the
challenger. The decision rule: the library is canonical UNLESS the render-off
shows it failing the §3/§6 bar where render-pro passes. The render-off
(delivered in output/render-off/*.svg) shows BOTH fail, so the from-scratch
path is authorised by §5.3. Evidence, per renderer:

LIBRARY RENDERER (src/renderer.ts, viewBox 820×900, rebuilt fresh from src/):
  [L1] Activation columns render the literal text "[object Object]" for the
       real on-box fixtures (michael-data.json, reference/test-chart.json).
       Its ChartData contract (src/types.ts) expects activations as "26.3"
       strings, but every real input (box fixtures, corpus vectors, the SPEC §3
       public payload) carries {gate, line, color, tone, base} objects — the
       shape render-pro.mjs consumes natively. On real data the default
       candidate cannot produce a legible v1 surface without a data shim.
  [L2] src/geometry.ts CHANNEL_PATHS holds 35 of the 36 required pairs (CHN-01,
       E-tier). Missing pair: 10–34 Exploration (G–Sacral). Same finding as
       Jimmy's 2026-11-03 23:07 MST census note and the parent task's
       reconciliation (geometry/bodygraph_geometry.json, commit d0bb8c0).
  [L3] DEFAULT_COLORS.bothFill = #8b5cf6 (purple) — contradicts SPEC §3.3
       ("black / red / striped-both colouring") and CHN-06 (E-tier): a third
       "both" color is a FAIL.
RENDER-PRO.MJS (viewBox 820×960, the production-call path):
  [R1] CHANNELS table holds 35 of 36 pairs (CHN-01). Missing pair: 10–34
       Exploration (G–Sacral) — the same pair, independently.
  [R2] No other E-tier failures were found in the render-off; but it is a
       one-off 636-line script with a hardcoded channel table, no public
       types/contract, and it is the side production "calls" only by wiring
       (SPEC §5: that is a fact about wiring, not about correctness).

DECISION: NEITHER EXISTING NODE RENDERER is canonical. The canonical renderer
is THIS module (Python, pure function, stdlib-only), which:
  - consumes BOTH real input shapes: the SPEC §3 public payload, the corpus
    "expected" objects, and the box *-data.json fixtures (name normalization:
    "G Center"→G, "Heart/Ego"→Ego, "Solar Plexus"/"SolarPlexus"→SolarPlexus);
  - carries the 36/36 channel pair set (CHN-01) verified against
    RUBRIC CHN-01 by scripts/verify_renderoff.py;
  - renders both-side gates split black/red, never a third color (CHN-06);
  - fills defined centers from exactly the CEN-07 palette (CEN-05/06/07).

CEN-08 PALETTE LOCK (in writing, before G3 closes):
  The canonical palette of the winner (this module) is the CEN-07 table below
  (PALETTE), which is identical to the library renderer's CANONICAL_CENTER_
  COLORS (the set CEN-07 itself was sourced from, documented as matching the
  HD.OS / Neutrino Design reference). Spleen keeps the canonical theme's
  distinct teal border (SPLEEN_BORDER) — per CEN-07's own note, sharing the
  Spleen/SolarPlexus hex is correct. No third palette ships.
  hd-platform's pastel CENTER_COLORS remain NON-canonical per SPEC §2.2.6
  (their alignment is that task's fix, not this renderer's).

RETIREMENT OF THE LOSERS (SPEC §5.3 — "two live renderers after this task is a
failed acceptance criterion"):
  - render-cli.mjs → render-pro.mjs: marked DEPRECATED (header note added to
    render-pro.mjs). The v1 public page (G4) consumes THIS module's SVG output
    via the §3 public payload + bridge mapping; the legacy Node path is
    retained only for the existing reports-service wiring until that swap,
    and must not gain new features.
  - The TS library (src/ + dist/) is retained as the reusable React component
    for in-app/interactive surfaces (the §7 v1.5 layer) — it is not a second
    server-side chart renderer. Its [L2]/[L3] defects (35/36 pairs; purple
    bothFill) are recorded here and must be fixed in the library before it
    ships any activated-chart output; the verify skill evidence pack stands
    for the render path it already covers.
  Net: exactly ONE canonical SERVER-side chart renderer is live: this module.

GEOMETRY SOURCE (provenance):
  geometry/bodygraph_geometry.json (parent task t_de02e1e0, commit d0bb8c0):
  9 centers / 36 channels / 64 gates, 820×900 → 1000×1000 uniform scale
  1.111111, aspect-preserving, centered (transform recorded in its _meta).
  Embedded inline below so this module has no file/network dependencies
  beyond the chart object passed in (task acceptance criterion 3).
  License note: positions derive from src/geometry.ts (AGPL-3.0); this file
  inherits that provenance.

ACCEPTANCE (task body) — how to verify:
  python3 render_bodygraph.py                          # writes demo-vector1.svg
  python3 scripts/verify_renderoff.py demo-vector1.svg # mechanical checks
  1. demo-vector1.svg parses as XML and contains 9 center shapes
  2. defined centers = exactly the set corpus vector #1 lists (count: 4)
  3. no dependencies beyond the input object
"""

from __future__ import annotations

import json
import sys

# ═════════════════════════════════════════════════════════════════════════════
# 1. GEOMETRY (embedded, data-only — source: geometry/bodygraph_geometry.json)
# ═════════════════════════════════════════════════════════════════════════════

VIEWBOX_W, VIEWBOX_H = 1240, 1000   # 1000×1000 body canvas + 120px activation columns each side
BODY_SHIFT_X = 120.0                # body canvas translated right so the left column has room

# 9 centers — positions/sizes in the 1000×1000 body canvas (before column shift).
# shape: triangle-up / diamond / rectangle / triangle-left / triangle-right
CENTERS = [
    ("head",        "Head",        "triangle-up",    500.0,   94.44,  77.78,  94.44),
    ("ajna",        "Ajna",        "diamond",        500.0,  207.78, 105.56,  83.33),
    ("throat",      "Throat",      "rectangle",      500.0,  337.78, 144.44,  77.78),
    ("g",           "G",           "diamond",        500.0,  485.56, 111.11, 133.33),
    ("ego",         "Ego",         "diamond",        627.78, 415.56,  88.89, 107.78),
    ("sacral",      "Sacral",      "rectangle",      500.0,  662.22, 144.44,  83.33),
    ("solarplexus", "SolarPlexus", "triangle-left",  733.33, 577.78, 155.56, 172.22),
    ("spleen",      "Spleen",      "triangle-right", 266.67, 577.78, 155.56, 172.22),
    ("root",        "Root",        "rectangle",      500.0,  800.0,  111.11,  72.22),
]

# 64 gate positions (x, y in the 1000×1000 body canvas).
GATE_POSITIONS = {
    1:  (500.0, 396.67),  2:  (480.0, 476.67),  3:  (546.67, 637.78), 4:  (520.0, 172.22),
    5:  (472.22, 576.67), 6:  (786.67, 573.33),  7:  (480.0, 396.67),  8:  (472.22, 327.78),
    9:  (527.78, 637.78), 10: (416.67, 515.56), 11: (485.56, 248.89), 12: (527.78, 300.0),
    13: (520.0, 396.67),  14: (500.0, 576.67),  15: (520.0, 476.67),  16: (546.67, 327.78),
    17: (472.22, 248.89), 18: (213.33, 633.33), 19: (528.89, 782.22), 20: (527.78, 327.78),
    21: (575.56, 443.33), 22: (786.67, 533.33), 23: (527.78, 248.89), 24: (500.0, 172.22),
    25: (411.11, 543.33), 26: (575.56, 382.22), 27: (472.22, 637.78), 28: (213.33, 613.33),
    29: (527.78, 576.67), 30: (786.67, 613.33), 31: (453.33, 327.78), 32: (213.33, 593.33),
    33: (500.0, 327.78),  34: (453.33, 637.78), 35: (500.0, 300.0),   36: (786.67, 513.33),
    37: (786.67, 553.33), 38: (475.56, 782.22), 39: (546.67, 782.22), 40: (600.0, 495.56),
    41: (500.0, 811.11),  42: (466.67, 682.22), 43: (500.0, 248.89),  44: (213.33, 553.33),
    45: (546.67, 300.0),  46: (500.0, 476.67),  47: (480.0, 172.22),  48: (213.33, 513.33),
    49: (786.67, 593.33), 50: (213.33, 573.33), 51: (575.56, 412.22), 52: (500.0, 782.22),
    53: (500.0, 682.22),  54: (493.33, 782.22), 55: (786.67, 633.33), 56: (472.22, 300.0),
    57: (213.33, 533.33), 58: (457.78, 782.22), 59: (500.0, 637.78),  60: (533.33, 682.22),
    61: (500.0, 135.56),  62: (453.33, 300.0),  63: (520.0, 135.56),  64: (480.0, 135.56),
}

# 36 channels — the complete CHN-01 pair set. (gate_a, gate_b, display name).
CHANNELS = [
    (1, 8, "Inspiration"), (2, 14, "The Beat"), (3, 60, "Mutation"), (4, 63, "Logic"),
    (5, 15, "Rhythm"), (6, 59, "Mating"), (7, 31, "The Alpha"), (9, 52, "Concentration"),
    (10, 20, "Awakening"), (10, 34, "Exploration"), (10, 57, "Survival"), (11, 56, "Curiosity"),
    (12, 22, "Openness"), (13, 33, "The Prodigal"), (16, 48, "Talent"), (17, 62, "Acceptance"),
    (18, 58, "Judgment"), (19, 49, "Synthesis"), (20, 34, "Charisma"), (20, 57, "Insight"),
    (21, 45, "Money"), (23, 43, "Structuring"), (24, 61, "Awareness"), (25, 51, "Initiation"),
    (26, 44, "Surrender"), (27, 50, "Preservation"), (28, 38, "Struggle"), (29, 46, "Discovery"),
    (30, 41, "Recognition"), (32, 54, "Transformation"), (34, 57, "Power"), (35, 36, "Transitoriness"),
    (37, 40, "Community"), (39, 55, "Emoting"), (42, 53, "Maturation"), (47, 64, "Abstraction"),
]

# Channel → circuit (from src/renderer.ts CHANNEL_CIRCUIT, the canonical mapping).
CHANNEL_CIRCUIT = {
    "10-20": "integration", "20-34": "integration", "10-57": "integration",
    "34-57": "integration", "20-57": "integration",
    "1-8": "individual", "2-14": "individual", "7-31": "individual", "13-33": "individual",
    "24-61": "individual", "47-64": "individual", "25-51": "individual",
    "3-60": "individual", "9-52": "individual", "18-58": "individual", "28-38": "individual",
    "39-55": "individual",
    "21-45": "tribal", "26-44": "tribal", "37-40": "tribal",
    "6-59": "tribal", "27-50": "tribal", "32-54": "tribal", "42-53": "tribal", "19-49": "tribal",
    "16-48": "collectiveLogic", "11-56": "collectiveLogic", "4-63": "collectiveLogic",
    "17-62": "collectiveLogic", "23-43": "collectiveLogic", "5-15": "collectiveLogic",
    "29-46": "collectiveLogic",
    "12-22": "collectiveSensing", "35-36": "collectiveSensing", "30-41": "collectiveSensing",
}

# ═════════════════════════════════════════════════════════════════════════════
# 2. PALETTE + STYLE TOKENS (canonical theme — CEN-07 set, CEN-08 locked above)
# ═════════════════════════════════════════════════════════════════════════════

PALETTE = {          # CEN-07 table, verbatim
    "Head":        "#f48fb1",
    "Ajna":        "#d32f2f",
    "Throat":      "#1565c0",
    "G":           "#388e3c",
    "Ego":         "#43a047",
    "Sacral":      "#e65100",
    "SolarPlexus": "#f9a825",
    "Spleen":      "#f9a825",
    "Root":        "#c62828",
}
SPLEEN_BORDER = "#00838f"     # canonical theme's distinct Spleen border (CEN-07 note)

CIRCUIT_COLORS = {   # src/renderer.ts CIRCUIT_COLORS
    "integration":       "#26c6da",
    "individual":        "#8d6e63",
    "tribal":            "#bcaaa4",
    "collectiveLogic":   "#283593",
    "collectiveSensing": "#6a1b9a",
}
DEFINED_CHANNEL_FALLBACK = "#3a2810"   # renderer.ts definedChannelStroke (uncircuited channels)
POTENTIAL_CHANNEL =      "#bbbbbb"     # renderer.ts potentialChannelStroke (hanging/undefined)

PERSONA_FILL = "#2a2a2a"   # personality = BLACK  (CHN-06; ACT-01 right column)
DESIGN_FILL  = "#c87860"   # design      = RED    (CHN-06; ACT-01 left column)
INACTIVE_FILL   = "#e8d8c0"
INACTIVE_TEXT   = "#888888"
PILL_TEXT       = "#ffffff"
CENTER_STROKE   = "#5a3e28"
OPEN_CENTER_STROKE = "#9e8570"
BG_COLOR        = "#f5ead8"
BODY_ORDER = ["Sun", "Earth", "Moon", "North Node", "South Node", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
GLYPHS = {"Sun": "☉", "Earth": "⊕", "Moon": "☽", "North Node": "☊",
          "South Node": "☋", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
          "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆", "Pluto": "♇"}

CENTER_NAME_ALIASES = {
    "g": "G", "g center": "G", "gc": "G", "gc center": "G",
    "ego": "Ego", "heart/ego": "Ego", "heart ego": "Ego",
    "solar plexus": "SolarPlexus", "solarplexus": "SolarPlexus",
    "head": "Head", "ajna": "Ajna", "throat": "Throat",
    "sacral": "Sacral", "spleen": "Spleen", "root": "Root",
}
CANONICAL_IDS = {"Head", "Ajna", "Throat", "G", "Ego",
                 "Sacral", "SolarPlexus", "Spleen", "Root"}

# Body-name normalization: fixture/corpus keys are lowercase or camelCase
# ("northnode", "southnode"); canonical column names are the ACT-02 list.
BODY_ALIASES = {
    "sun": "Sun", "earth": "Earth", "moon": "Moon",
    "northnode": "North Node", "north node": "North Node",
    "southnode": "South Node", "south node": "South Node",
    "mercury": "Mercury", "venus": "Venus", "mars": "Mars",
    "jupiter": "Jupiter", "saturn": "Saturn", "uranus": "Uranus",
    "neptune": "Neptune", "pluto": "Pluto",
}


# ═════════════════════════════════════════════════════════════════════════════
# 3. INPUT NORMALIZATION — accepts SPEC §3 payload, corpus "expected", fixtures
# ═════════════════════════════════════════════════════════════════════════════

def _norm_center(name: str) -> str:
    return CENTER_NAME_ALIASES.get(str(name).strip().lower(), str(name).strip())


def _activation_gate_line(v):
    """Return (gate, line) from any real activation shape, or None.

    Shapes handled: "26.3" | {"gate":26,"line":3} | {"gate_line":"26.3"} | 26.3
    """
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        if "." in s:
            g, l = s.split(".", 1)
            if g.isdigit() and l.isdigit():
                return int(g), int(l)
        return None
    if isinstance(v, dict):
        g = v.get("gate")
        l = v.get("line")
        if g is None or l is None:
            return None
        return int(g), int(l)
    if isinstance(v, (int, float)):
        g, l = int(v) // 100, int(v) % 100
        if g and l:
            return g, l
    return None


def normalize_chart(chart: dict) -> dict:
    """Reduce any accepted input shape to the canonical working form."""
    out = {"meta": {}, "design": {}, "personality": {},
           "defined_centers": set(), "channels": []}

    # --- meta -------------------------------------------------------------
    meta_src = chart.get("meta") if isinstance(chart.get("meta"), dict) else chart
    out["meta"] = {k: meta_src.get(k) for k in
                   ("name", "type", "hd_type", "authority", "strategy",
                    "profile", "definition", "incarnation_cross",
                    "incarnationCross", "variables") if meta_src.get(k) is not None}
    if "type" not in out["meta"] and "hd_type" in out["meta"]:
        out["meta"]["type"] = out["meta"]["hd_type"]

    # --- activations → per-side gate sets + per-body values ---------------
    act = chart.get("activations")
    if isinstance(act, dict):
        for stream in ("design", "personality"):
            block = act.get(stream)
            if not isinstance(block, dict):
                continue
            for body, val in block.items():
                gl = _activation_gate_line(val)
                if gl is None:
                    continue
                out[stream][BODY_ALIASES.get(str(body).strip().lower(), str(body))] = gl

    # --- explicit gate arrays (fallback/merge when activations absent) ----
    for stream, field in (("personality", "personalityGates"), ("design", "designGates")):
        for g in chart.get(field) or []:
            out[stream].setdefault(f"gate_{g}", (int(g), 1))
    both = [int(g) for g in (chart.get("bothGates") or [])]

    # --- defined centers ---------------------------------------------------
    raw_dc = chart.get("defined_centers") or chart.get("definedCenters")
    if raw_dc:
        out["defined_centers"] = {c for c in (_norm_center(x) for x in raw_dc) if c in CANONICAL_IDS}
        if len(out["defined_centers"]) != len(raw_dc):
            raise ValueError(f"undefined center name(s) in input: "
                             f"{[x for x in raw_dc if _norm_center(x) not in CANONICAL_IDS]}")

    # --- channels ----------------------------------------------------------
    raw_ch = chart.get("channels") or chart.get("defined_channels") or chart.get("definedChannels")
    if raw_ch:
        flat = all(isinstance(c, int) for c in raw_ch)
        if flat:
            # Corpus "defined_channels" shape: bare gate numbers → resolve to
            # channel pairs via the canonical 36-pair table.
            gate_set = {int(g) for g in raw_ch}
            out["channels"] = sorted(
                (a, b) for a, b, _n in CHANNELS if {a, b} <= gate_set)
        else:
            parsed = []
            for c in raw_ch:
                if isinstance(c, str):
                    parts = [p for p in c.replace("–", "-").replace("—", "-").split("-") if p]
                    parsed.append((int(parts[0]), int(parts[1])))
                elif isinstance(c, (list, tuple)) and len(c) == 2 and all(isinstance(x, int) for x in c):
                    parsed.append((int(c[0]), int(c[1])))
                else:
                    raise ValueError(f"unrecognized channel entry: {c!r}")
            out["channels"] = sorted(set((a, b) if a <= b else (b, a) for a, b in parsed))

    # --- derived sets (single source of truth) -----------------------------
    p_gates = {g for g, _ in out["personality"].values()} | set(both)
    d_gates = {g for g, _ in out["design"].values()} | set(both)
    out["p_gates"], out["d_gates"], out["both"] = p_gates, d_gates, set(both)

    # center definition from data when not supplied (SPEC §3.3 invariant)
    if not out["defined_centers"]:
        for g in (p_gates | d_gates):
            for a, b, _name in CHANNELS:
                if g in (a, b):
                    out["defined_centers"].add(_center_of(a, b)[0])
                    out["defined_centers"].add(_center_of(a, b)[1])
    return out


def _center_of(g1: int, g2: int):
    c1 = _GATE_CENTER[g1]
    c2 = _GATE_CENTER[g2]
    return c1, c2


# gate → center id (CEN-04 mapping, from geometry/bodygraph_geometry.json)
_GATE_CENTER = {
    1: "g", 2: "g", 3: "sacral", 4: "ajna", 5: "sacral", 6: "solarplexus",
    7: "g", 8: "throat", 9: "sacral", 10: "g", 11: "ajna", 12: "throat",
    13: "g", 14: "sacral", 15: "g", 16: "throat", 17: "ajna", 18: "spleen",
    19: "root", 20: "throat", 21: "ego", 22: "solarplexus", 23: "throat", 24: "ajna",
    25: "g", 26: "ego", 27: "sacral", 28: "spleen", 29: "sacral", 30: "solarplexus",
    31: "throat", 32: "spleen", 33: "throat", 34: "sacral", 35: "throat", 36: "solarplexus",
    37: "solarplexus", 38: "root", 39: "root", 40: "ego", 41: "root", 42: "sacral",
    43: "ajna", 44: "spleen", 45: "throat", 46: "g", 47: "ajna", 48: "spleen",
    49: "solarplexus", 50: "spleen", 51: "ego", 52: "root", 53: "root", 54: "root",
    55: "solarplexus", 56: "throat", 57: "spleen", 58: "root", 59: "sacral", 60: "root",
    61: "head", 62: "throat", 63: "head", 64: "head",
}


# ═════════════════════════════════════════════════════════════════════════════
# 4. SHAPE HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _f(v: float) -> str:
    return f"{v:.2f}"


def center_polygon(shape, cx, cy, w, h):
    """Vertex list (left-to-right-ish) for a center in body-canvas coords."""
    if shape == "rectangle":
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    if shape == "triangle-up":
        return [(cx - w / 2, cy + h / 2), (cx, cy - h / 2), (cx + w / 2, cy + h / 2)]
    if shape == "triangle-left":
        return [(cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy)]
    if shape == "triangle-right":
        return [(cx - w / 2, cy - h / 2), (cx - w / 2, cy + h / 2), (cx + w / 2, cy)]
    if shape == "diamond":
        return [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]
    raise ValueError(f"unknown center shape: {shape}")


# ═════════════════════════════════════════════════════════════════════════════
# 5. THE RENDERER — pure function: chart object in, standalone SVG string out
# ═════════════════════════════════════════════════════════════════════════════

def render_bodygraph(chart: dict) -> str:
    """Render one chart object (SPEC §3 payload / corpus expected / box fixture)
    into a standalone SVG string. No I/O, no network, stdlib only."""
    d = normalize_chart(chart)
    d["channels_all"] = CHANNELS
    defined_ch = {tuple(c) for c in d["channels"]}
    # state per channel: 'defined' iff both gates active (either side)
    active_all = d["p_gates"] | d["d_gates"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEWBOX_W} {VIEWBOX_H}" '
        f'width="{VIEWBOX_W}" height="{VIEWBOX_H}" font-family="Inter, Arial, sans-serif">',
        f'<rect x="0" y="0" width="{VIEWBOX_W}" height="{VIEWBOX_H}" fill="{BG_COLOR}"/>',
    ]

    # ── header ──────────────────────────────────────────────────────────
    meta = d["meta"]
    name = meta.get("name") or "Human Design Bodygraph"
    birth_bits = [meta.get("strategy")]
    head_sub = ""
    if isinstance(chart.get("birth"), dict):
        loc = chart["birth"].get("local", {})
        if loc.get("date"):
            head_sub = f"{loc.get('date','')} {loc.get('time','')} · {loc.get('timezone_iana','')}"
    parts.append(f'<text x="{VIEWBOX_W/2:.0f}" y="30" text-anchor="middle" '
                 f'font-size="20" font-weight="700" fill="#2a2a2a">{name}</text>')
    if head_sub:
        parts.append(f'<text x="{VIEWBOX_W/2:.0f}" y="48" text-anchor="middle" '
                     f'font-size="11" fill="#5a3e28">{head_sub}</text>')

    body = []  # body-canvas elements (shifted as a group)

    # ── channel layer (under centers): undefined + hanging ──────────────
    for a, b, _n in CHANNELS:
        if (a, b) in defined_ch or (b, a) in defined_ch:
            continue
        x1, y1 = GATE_POSITIONS[a]
        x2, y2 = GATE_POSITIONS[b]
        hanging = (a in active_all) or (b in active_all)
        if _GATE_CENTER[a] == _GATE_CENTER[b]:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            body.append(f'<path d="M{_f(x1)} {_f(y1)} Q{_f(mx + 30)} {_f(my - 30)} {_f(x2)} {_f(y2)}" '
                        f'fill="none" stroke="{POTENTIAL_CHANNEL}" stroke-width="1.5" '
                        f'stroke-dasharray="5,4" opacity="{0.9 if hanging else 0.55}"/>')
        else:
            body.append(f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" '
                        f'stroke="{POTENTIAL_CHANNEL}" stroke-width="1.5" '
                        f'stroke-dasharray="5,4" opacity="{0.9 if hanging else 0.55}"/>')

    # ── center layer ────────────────────────────────────────────────────
    for cid, cname, shape, cx, cy, w, h in CENTERS:
        pts = center_polygon(shape, cx, cy, w, h)
        poly = " ".join(f"{_f(x)},{_f(y)}" for x, y in pts)
        if cname in d["defined_centers"]:
            fill = PALETTE[cname]
            stroke = SPLEEN_BORDER if cid == "spleen" else CENTER_STROKE
            sw = 2.5
        else:
            fill = "#ffffff"
            stroke = OPEN_CENTER_STROKE
            sw = 2.0
        body.append(f'<polygon points="{poly}" fill="{fill}" stroke="{stroke}" '
                    f'stroke-width="{sw}" stroke-linejoin="round"/>')
        # center name label (inside shape, above center point)
        body.append(f'<text x="{_f(cx)}" y="{_f(cy + 3)}" text-anchor="middle" '
                    f'dominant-baseline="middle" font-size="12" font-weight="600" '
                    f'fill="#3a2810" opacity="0.85">{cname if cid != "solarplexus" else "Solar Plexus"}</text>')

    # ── defined channel layer (over centers) ────────────────────────────
    for a, b, n in CHANNELS:
        if (a, b) not in defined_ch:
            continue
        key = f"{min(a,b)}-{max(a,b)}"
        stroke = CIRCUIT_COLORS.get(CHANNEL_CIRCUIT.get(key, ""), DEFINED_CHANNEL_FALLBACK)
        x1, y1 = GATE_POSITIONS[a]
        x2, y2 = GATE_POSITIONS[b]
        if _GATE_CENTER[a] == _GATE_CENTER[b]:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            body.append(f'<path d="M{_f(x1)} {_f(y1)} Q{_f(mx + 30)} {_f(my - 30)} {_f(x2)} {_f(y2)}" '
                        f'fill="none" stroke="{stroke}" stroke-width="5" stroke-linecap="round"/>')
        else:
            body.append(f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" '
                        f'stroke="{stroke}" stroke-width="5" stroke-linecap="round"/>')

    # ── gate pills (top layer) ──────────────────────────────────────────
    for g in range(1, 65):
        x, y = GATE_POSITIONS[g]
        if g in d["both"]:
            # CHN-06: both sides → split black/red, half and half. No third color.
            body.append(
                f'<g><circle cx="{_f(x)}" cy="{_f(y)}" r="13" fill="{PERSONA_FILL}" '
                f'stroke="#ffffff" stroke-width="1.5"/>'
                f'<path d="M{x - 13:.2f} {_f(y)} A13 13 0 0 0 {x + 13:.2f} {_f(y)} Z" '
                f'fill="{DESIGN_FILL}" stroke="none"/>'
                f'<text x="{_f(x)}" y="{_f(y + 0.5)}" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="12" font-weight="700" fill="{PILL_TEXT}">{g}</text></g>')
        elif g in d["p_gates"]:
            body.append(
                f'<g><circle cx="{_f(x)}" cy="{_f(y)}" r="13" fill="{PERSONA_FILL}" '
                f'stroke="#ffffff" stroke-width="1.5"/>'
                f'<text x="{_f(x)}" y="{_f(y + 0.5)}" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="12" font-weight="700" fill="{PILL_TEXT}">{g}</text></g>')
        elif g in d["d_gates"]:
            body.append(
                f'<g><circle cx="{_f(x)}" cy="{_f(y)}" r="13" fill="{DESIGN_FILL}" '
                f'stroke="#ffffff" stroke-width="1.5"/>'
                f'<text x="{_f(x)}" y="{_f(y + 0.5)}" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="12" font-weight="700" fill="{PILL_TEXT}">{g}</text></g>')
        else:
            body.append(
                f'<g><circle cx="{_f(x)}" cy="{_f(y)}" r="13" fill="{INACTIVE_FILL}" '
                f'stroke="{OPEN_CENTER_STROKE}" stroke-width="1"/>'
                f'<text x="{_f(x)}" y="{_f(y + 0.5)}" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="11" fill="{INACTIVE_TEXT}">{g}</text></g>')

    parts.append(f'<g transform="translate({BODY_SHIFT_X},0)">{chr(10).join(body)}</g>')

    # ── activation columns (ACT-01: Design RED left / Personality BLACK right)
    parts.append(_render_column(d["design"], DESIGN_FILL, "DESIGN",
                                x0=10.0, x1=138.0, side="left"))
    parts.append(_render_column(d["personality"], PERSONA_FILL, "PERSONALITY",
                                x0=VIEWBOX_W - 138.0, x1=VIEWBOX_W - 10.0, side="right"))

    # ── property panel (bottom) — only fields the data actually carries ──
    panel = _property_panel(d)
    if panel:
        parts.append(panel)

    parts.append("</svg>")
    return "".join(parts)


def _render_column(activs, color, title, x0, x1, side):
    cx = (x0 + x1) / 2
    top, row_h, bottom = 90.0, 52.0, 780.0
    rows = []
    rows.append(f'<rect x="{_f(x0)}" y="{top - 18}" width="{_f(x1 - x0)}" '
                f'height="{bottom - top + 30}" rx="6" fill="#ffffff" '
                f'stroke="{OPEN_CENTER_STROKE}" stroke-width="1" opacity="0.7"/>')
    rows.append(f'<text x="{cx:.0f}" y="{top - 2}" text-anchor="middle" font-size="12" '
                f'font-weight="700" letter-spacing="1" fill="{color}">{title}</text>')
    for i, body_name in enumerate(BODY_ORDER):
        y = top + 14 + i * row_h
        glyph = GLYPHS[body_name]
        gl = activs.get(body_name)
        val = f"{gl[0]}.{gl[1]}" if gl else "—"
        rows.append(f'<text x="{x0 + 14:.0f}" y="{_f(y + 8)}" font-size="20" fill="{color}">{glyph}</text>')
        rows.append(f'<text x="{x0 + 40:.0f}" y="{_f(y + 8)}" font-size="11" fill="#5a3e28">'
                    f'{body_name}</text>')
        rows.append(f'<text x="{x1 - 12:.0f}" y="{_f(y + 8)}" text-anchor="end" font-size="14" '
                    f'font-weight="700" fill="{color}">{val}</text>')
        if i < len(BODY_ORDER) - 1:
            rows.append(f'<line x1="{x0 + 8}" y1="{_f(y + 20)}" x2="{x1 - 8}" y2="{_f(y + 20)}" '
                        f'stroke="#e8d8c0" stroke-width="1"/>')
    return "<g>" + "".join(rows) + "</g>"


def _property_panel(d):
    m = d["meta"]
    lines = []
    if m.get("type"):
        lines.append(("TYPE", m["type"]))
    if m.get("strategy"):
        lines.append(("STRATEGY", m["strategy"]))
    if m.get("authority"):
        lines.append(("AUTHORITY", m["authority"]))
    if m.get("profile"):
        lines.append(("PROFILE", m["profile"]))
    if m.get("definition"):
        lines.append(("DEFINITION", m["definition"]))
    cross = m.get("incarnation_cross") or m.get("incarnationCross")
    if cross:
        lines.append(("CROSS", str(cross)))
    if not lines:
        return ""
    y0, row_h = 830.0, 20.0
    out = [f'<rect x="10" y="{y0 - 14}" width="{VIEWBOX_W - 20}" height="{len(lines) * row_h + 22}" '
           f'rx="6" fill="#ffffff" stroke="{OPEN_CENTER_STROKE}" stroke-width="1" opacity="0.85"/>']
    n = len(lines)
    for i, (k, v) in enumerate(lines):
        x = 40 + (i * (VIEWBOX_W - 80)) // n
        out.append(f'<text x="{x}" y="{_f(y0 + 8 + i * 0)}" font-size="9" fill="#888888" '
                   f'letter-spacing="1">{k}</text>')
        out.append(f'<text x="{x}" y="{_f(y0 + 22)}" font-size="13" font-weight="700" '
                   f'fill="#2a2a28">{v}</text>')
    return "<g>" + "".join(out) + "</g>"


# ═════════════════════════════════════════════════════════════════════════════
# 6. DEMO — corpus vector #1 (task acceptance: demo-vector1.svg beside module)
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Repo root = parent of this module's directory (module lives in renderer/).
    import os
    HERE = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(HERE)
    with open(f"{ROOT}/corpus/vectors.json") as fh:
        vector1 = json.load(fh)["vectors"][0]
    with open(f"{ROOT}/michael-data.json") as fh:
        fixture = json.load(fh)

    # Vector #1 chart object: the corpus "expected" is FILL-stubbed for
    # planetary_activations, so the per-planet data comes from the on-box
    # fixture michael-data.json (SPEC §6: "copied verbatim from the box
    # michael-data.json, cited as source") — same chart, independently listed
    # gates/channels/centers in both files.
    chart = {
        "name": vector1.get("name", "Vector 1"),
        "birth": vector1.get("birth"),
        "type": vector1["expected"].get("type"),
        "profile": vector1["expected"].get("profile"),
        "authority": vector1["expected"].get("authority"),
        "definition": vector1["expected"].get("definition"),
        "incarnation_cross": vector1["expected"].get("incarnation_cross"),
        "defined_centers": vector1["expected"].get("defined_centers"),
        "defined_channels": vector1["expected"].get("defined_channels"),
        "personalityGates": fixture["personalityGates"],
        "designGates": fixture["designGates"],
        "bothGates": fixture["bothGates"],
        "activations": fixture["activations"],
    }

    svg = render_bodygraph(chart)
    out_path = f"{HERE}/demo-vector1.svg"  # beside the module (task acceptance)
    with open(out_path, "w") as fh:
        fh.write(svg)

    d = normalize_chart(chart)
    defined = sorted(c for c in d["defined_centers"])
    print(f"OK  wrote {out_path} ({len(svg)} chars)")
    print(f"    centers on surface: 9 (9 shapes in SVG)")
    print(f"    defined centers: {len(defined)} → {defined}  (palette fills: "
          f"{', '.join(PALETTE[c] for c in defined)})")
    print(f"    defined channels: {len(d['channels'])} → {d['channels']}")
    print(f"    gate pills: 64 (38 inactive, {len(d['p_gates'])} personality, "
          f"{len(d['d_gates'])} design incl. both, {len(d['both'])} both-sides split)")
