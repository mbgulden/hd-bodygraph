#!/usr/bin/env python3
"""
build_geometry.py — one-shot generator for bodygraph_geometry.json

Derives pure HD bodygraph geometry (data only, no drawing code) from the
two on-box authorities named in the task:

  * GEOMETRY / POSITIONS SOURCE (research-recommended, SPEC §5 default):
      /home/ubuntu/work/hd-bodygraph/src/geometry.ts
      -> center shapes (name/type/cx/cy/w/h) + all 64 gate (x,y) positions
      -> viewBox 820x900

  * WHEEL / TOPOLOGY SOURCE (canonical HD mapping):
      /home/ubuntu/work/OpenHumanDesignMCP/hd-mcp-server/src/matrix_mapper.py
      -> GATE_CENTER  : authoritative gate -> center for all 64 gates
      -> CHANNELS     : the canonical 36-channel table (dedup of 37 raw)

geometry.ts carries 35 channel paths; the engine's canonical table has 36.
The missing one (10-34 "Exploration", G<->Sacral) is added from the engine
so the deliverable is the full 36.

Coordinate space: rescaled from 820x900 to a 1000x1000 viewBox using a
UNIFORM scale (1000/900) so aspect ratio is preserved, then the content is
centered horizontally. This transform is recorded in _meta.
"""
import json, re, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)  # /home/ubuntu/work/hd-bodygraph

GEOM_TS   = os.path.join(REPO, "src", "geometry.ts")
ENGINE_MM = "/home/ubuntu/work/OpenHumanDesignMCP/hd-mcp-server/src/matrix_mapper.py"

SRC_W, SRC_H = 820.0, 900.0
DST_W, DST_H = 1000.0, 1000.0
SCALE = DST_H / SRC_H                      # uniform, fit-to-height
CONTENT_W = SRC_W * SCALE                  # 911.11
X_OFFSET = (DST_W - CONTENT_W) / 2.0       # center horizontally

def sx(x): return round(X_OFFSET + x * SCALE, 2)
def sy(y): return round(y * SCALE, 2)
def sww(w): return round(w * SCALE, 2)

# ---- parse geometry.ts: centers + gate positions ----
src = open(GEOM_TS).read()
centers = re.findall(
    r"name:\s*'(\w+)',\s*type:\s*'([\w-]+)',\s*cx:\s*(\d+),\s*cy:\s*(\d+),\s*w:\s*(\d+),\s*h:\s*(\d+)",
    src)
gates_src = re.findall(r"gate:\s*(\d+),\s*x:\s*(\d+),\s*y:\s*(\d+)", src)

NAME_SLUG = {
    "Head": "head", "Ajna": "ajna", "Throat": "throat", "G": "g",
    "Ego": "ego", "Sacral": "sacral", "SolarPlexus": "solarplexus",
    "Spleen": "spleen", "Root": "root",
}
# engine uses these two names that differ from geometry.ts -> map to geometry.ts names
ENGINE_TO_GEOM = {"Heart/Ego": "Ego", "Solar Plexus": "SolarPlexus"}

# ---- parse engine: GATE_CENTER + CHANNELS ----
em = open(ENGINE_MM).read()
gc_match = re.search(r"GATE_CENTER\s*=\s*\{(.*?)\n\}", em, re.S)
if not gc_match:
    raise SystemExit("ERROR: GATE_CENTER block not found in matrix_mapper.py")
gc_block = gc_match.group(1)
gate_center_engine = {int(g): n.strip() for g, n in re.findall(r'(\d+)\s*:\s*"([^"]+)"', gc_block)}
gate_center = {g: (ENGINE_TO_GEOM.get(n, n)) for g, n in gate_center_engine.items()}

ch_match = re.search(r"CHANNELS\s*=\s*\{(.*?)\n\}", em, re.S)
if not ch_match:
    raise SystemExit("ERROR: CHANNELS block not found in matrix_mapper.py")
ch_block = ch_match.group(1)
raw_pairs = re.findall(r'\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*:\s*"([^"]+)"', ch_block)
seen, channels = set(), []
for a, b, name in raw_pairs:
    key = frozenset((int(a), int(b)))
    if key in seen:
        continue
    seen.add(key)
    channels.append((key, name))

assert len(gate_center) == 64, f"engine gate map must cover 64, got {len(gate_center)}"
assert len(channels) == 36, f"canonical channel table must be 36 unique, got {len(channels)}"

# ---- build centers list ----
centers_out = []
for name, shape, cx, cy, w, h in centers:
    slug = NAME_SLUG[name]
    centers_out.append({
        "id": slug,
        "name": name,
        "shape": shape,
        "cx": sx(float(cx)),
        "cy": sy(float(cy)),
        "w": sww(float(w)),
        "h": sww(float(h)),
    })
center_id_by_name = {c["name"]: c["id"] for c in centers_out}

# ---- build gates list (position from geometry.ts, center from engine) ----
gate_pos = {int(g): (float(x), float(y)) for g, x, y in gates_src}
assert len(gate_pos) == 64, f"geometry.ts must position 64 gates, got {len(gate_pos)}"
gates_out = []
for num in range(1, 65):
    gx, gy = gate_pos[num]
    cname = gate_center[num]
    gates_out.append({
        "number": num,
        "center": center_id_by_name[cname],
        "x": sx(gx),
        "y": sy(gy),
    })

# ---- build channels list (36, from engine; endpoints = the two gate positions) ----
channels_out = []
for i, (key, name) in enumerate(sorted(channels, key=lambda t: min(t[0])), 1):
    a, b = sorted(key)
    ca = center_id_by_name[gate_center[a]]
    cb = center_id_by_name[gate_center[b]]
    pa = (sx(gate_pos[a][0]), sy(gate_pos[a][1]))
    pb = (sx(gate_pos[b][0]), sy(gate_pos[b][1]))
    channels_out.append({
        "id": i,
        "name": name,
        "gates": [a, b],
        "center_pair": [ca, cb],
        "path_endpoints": [pa, pb],
    })

# ---- _meta with source + license attribution ----
doc = {
    "_meta": {
        "artifact": "bodygraph_geometry",
        "kind": "data-only geometry (no drawing code)",
        "source": {
            "geometry_positions": {
                "name": "On-box bodygraph renderer library (src/geometry.ts + src/renderer.ts)",
                "path": GEOM_TS,
                "note": "Recommended by RESEARCH-technical-resources.md §3.6/§5.2 and SPEC.md §5 "
                        "(the box library renderer is the canonical default).",
            },
            "wheel_topology": {
                "name": "OpenHumanDesignMCP canonical HD mapping (matrix_mapper.py)",
                "path": ENGINE_MM,
                "note": "Authoritative gate->center (GATE_CENTER) and 36-channel table (CHANNELS).",
            },
        },
        "license": "AGPL-3.0",
        "license_note": "geometry.ts / renderer.ts live in the on-box hd-bodygraph prototype, part of the "
                        "AGPL-3.0 GrowthWeb HD platform (per RESEARCH-technical-resources.md §3.6 'Own/AGPL platform'). "
                        "No third-party/public-domain SVG template was used. Michael confirms any license change.",
        "viewbox": {"source": {"width": 820, "height": 900},
                    "target": {"width": 1000, "height": 1000}},
        "transform": {
            "method": "uniform-scale then center",
            "scale": round(SCALE, 6),
            "x_offset": round(X_OFFSET, 2),
            "x_prime": "x' = x_offset + x * scale",
            "y_prime": "y' = y * scale",
            "aspect_ratio_preserved": True,
        },
        "counts": {"centers": len(centers_out), "channels": len(channels_out), "gates": len(gates_out)},
        "reconciliation": "geometry.ts carries 35 channel paths; the engine's canonical table has 36. "
                          "The missing channel (10-34 'Exploration', G<->Sacral) is added from the engine "
                          "so the deliverable is the complete 36-channel set.",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    },
    "centers": centers_out,
    "channels": channels_out,
    "gates": gates_out,
}

out = os.path.join(HERE, "bodygraph_geometry.json")
with open(out, "w") as f:
    json.dump(doc, f, indent=2)
    f.write("\n")
print("wrote", out)
print("centers=%d channels=%d gates=%d" % (len(centers_out), len(channels_out), len(gates_out)))
