#!/usr/bin/env python3
"""
Bridge: OpenHumanDesignMCP Engine → Gonzih hd-bodygraph SVG.

Computes natal chart via pyswisseph, maps to ChartData JSON,
then calls the Node.js renderer to produce an SVG bodygraph.

Usage:
    python3 bridge.py --name "Test" --year 1989 --month 11 --day 29 --hour 9 --minute 0 --location "UTC"
    python3 bridge.py --file input.json          # bulk from JSON array
    python3 bridge.py --serve --port 8001         # HTTP server mode
"""

import argparse, json, os, subprocess, sys, tempfile
from datetime import datetime

# Add MCP engine to path
ENGINE_PATH = os.environ.get(
    "ENGINE_PATH", "/home/ubuntu/work/OpenHumanDesignMCP/hd-mcp-server/src"
)
sys.path.insert(0, ENGINE_PATH)

from cosmic_calculator import calculate_natal_chart
from ephemeris_engine import init_ephemeris
from geo_resolver import resolve_location, local_to_utc

# Ensure ephemeris is initialized once
init_ephemeris()

# ── Mapping: MCP Engine → Gonzih ChartData ─────────────────────────────

# Our engine uses "Heart" for the Ego center
CENTER_ALIASES = {
    "Heart": "Ego",
    "Heart/Ego": "Ego",
    "Ego/Heart": "Ego",
    "Solar Plexus": "SolarPlexus",
}

def _norm_center(name: str) -> str:
    # Handle compound names like "Heart/Ego" or just "Heart"
    for alias, canonical in CENTER_ALIASES.items():
        if alias in name:
            return canonical
    return name

def _make_birth_dt(year, month, day, hour):
    h = int(hour)
    m = int((hour - h) * 60)
    s = int(((hour - h) * 60 - m) * 60)
    return datetime(year, month, day, h, m, s)

def compute_chart(name, year, month, day, hour, minute, location="UTC", lat=0.0, lon=0.0):
    """Compute natal chart and return MCP engine result dict."""
    hour_dec = hour + minute / 60.0
    
    geo = resolve_location(location) if location and location != "UTC" else None
    use_lat = lat if lat != 0 else (geo["lat"] if geo else 0)
    use_lon = lon if lon != 0 else (geo["lon"] if geo else 0)
    use_tz = geo["timezone"] if geo else "UTC"
    
    utc = local_to_utc(year, month, day, hour_dec, location) if geo else (year, month, day, hour_dec)
    birth_dt = _make_birth_dt(utc[0], utc[1], utc[2], utc[3])
    
    chart = calculate_natal_chart(
        name=name, birth_dt=birth_dt,
        lat=use_lat, lon=use_lon, timezone=use_tz,
    )
    return chart

def chart_to_gonzih(chart: dict) -> dict:
    """Convert MCP engine chart dict to Gonzih ChartData JSON."""
    
    defined_centers = [_norm_center(c) for c in chart.get("defined_centers", [])]
    
    # Build personality/design gate sets
    personality_gates = []
    design_gates = []
    both_gates = []
    
    pers_planets = chart.get("personality_planets", {})
    des_planets = chart.get("design_planets", {})
    
    pers_gate_set = set()
    for p, data in pers_planets.items():
        if isinstance(data, dict) and data.get("gate"):
            pers_gate_set.add(data["gate"])
    
    des_gate_set = set()
    for p, data in des_planets.items():
        if isinstance(data, dict) and data.get("gate"):
            des_gate_set.add(data["gate"])
    
    # Classify gates
    for g in pers_gate_set | des_gate_set:
        if g in pers_gate_set and g in des_gate_set:
            both_gates.append(g)
        elif g in pers_gate_set:
            personality_gates.append(g)
        else:
            design_gates.append(g)
    
    # Build gate activations list
    gates = []
    all_gates = set()
    for g in personality_gates:
        gates.append({"gate": g, "coloring": "personality"})
        all_gates.add(g)
    for g in design_gates:
        gates.append({"gate": g, "coloring": "design"})
        all_gates.add(g)
    for g in both_gates:
        gates.append({"gate": g, "coloring": "both"})
        all_gates.add(g)
    
    # Add inactive gates for completeness
    for g in range(1, 65):
        if g not in all_gates:
            gates.append({"gate": g, "coloring": "inactive"})
    
    # Channels
    channels = []
    for ch in chart.get("defined_channels", []):
        g = ch.get("gates", ())
        if len(g) == 2:
            channels.append([g[0], g[1]])
    
    # Planetary activations (gate.line format)
    def _planet_activations(planets: dict) -> dict:
        result = {}
        for planet, data in planets.items():
            if isinstance(data, dict):
                gate = data.get("gate", "")
                line = data.get("line", "")
                if gate:
                    result[planet.lower().replace(" ", "")] = f"{gate}.{line}" if line else str(gate)
        return result
    
    activations = {
        "design": _planet_activations(des_planets),
        "personality": _planet_activations(pers_planets),
    }
    
    result = {
        "definedCenters": defined_centers,
        "personalityGates": sorted(personality_gates),
        "designGates": sorted(design_gates),
        "bothGates": sorted(both_gates),
        "gates": sorted(gates, key=lambda x: x["gate"]),
        "channels": channels,
        "type": chart.get("hd_type", ""),
        "profile": str(chart.get("profile", "")),
        "definition": chart.get("definition", ""),
        "authority": chart.get("authority", ""),
        "strategy": chart.get("strategy", ""),
        "activations": activations,
    }
    return result


def render_svg(chart_data: dict, theme: str = "canonical") -> str:
    """Take ChartData dict, call Node.js renderer, return SVG string."""
    # Write chart data to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(chart_data, f)
        tmp_path = f.name
    
    renderer_dir = os.path.dirname(os.path.abspath(__file__))
    render_script = os.path.join(renderer_dir, "render-cli.mjs")
    
    try:
        result = subprocess.run(
            ["node", render_script, tmp_path, theme],
            capture_output=True, text=True, timeout=15,
            cwd=renderer_dir,
        )
        if result.returncode != 0:
            print(f"Renderer error: {result.stderr}", file=sys.stderr)
            return ""
        return result.stdout
    finally:
        os.unlink(tmp_path)


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="HD Bodygraph Bridge")
    parser.add_argument("--name", default="Unknown")
    parser.add_argument("--year", type=int, required=False)
    parser.add_argument("--month", type=int, required=False)
    parser.add_argument("--day", type=int, required=False)
    parser.add_argument("--hour", type=int, default=12)
    parser.add_argument("--minute", type=int, default=0)
    parser.add_argument("--location", default="UTC")
    parser.add_argument("--lat", type=float, default=0.0)
    parser.add_argument("--lon", type=float, default=0.0)
    parser.add_argument("--theme", default="canonical", choices=["default", "canonical"])
    parser.add_argument("--output", "-o", help="Output SVG file path")
    parser.add_argument("--json", action="store_true", help="Output ChartData JSON instead of SVG")
    args = parser.parse_args()
    
    if not args.year:
        parser.error("--year is required")
    
    chart = compute_chart(
        name=args.name, year=args.year, month=args.month, day=args.day,
        hour=args.hour, minute=args.minute,
        location=args.location, lat=args.lat, lon=args.lon,
    )
    
    gonzih_data = chart_to_gonzih(chart)
    
    if args.json:
        print(json.dumps(gonzih_data, indent=2))
        return
    
    svg = render_svg(gonzih_data, args.theme)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(svg)
        print(f"Saved to {args.output}")
    else:
        print(svg)


if __name__ == "__main__":
    main()
