#!/usr/bin/env python3
"""
smoke_check.py — validates bodygraph_geometry.json.

Checks (data only, no rendering):
  1. The file parses as JSON.
  2. _meta carries a source + license attribution.
  3. counts: 9 centers, 36 channels, 64 gates.
  4. every channel's two gates each belong to one of the channel's two centers.
  5. every gate 1..64 appears exactly once in its center assignment.
  6. center counts per center sum to 64; channel center-pairs reference real centers.

Prints PASS/FAIL + counts. Exit 0 on PASS, 1 on FAIL.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "bodygraph_geometry.json")

failures = []
def check(cond, msg):
    if not cond:
        failures.append(msg)

def main():
    # 1. parse
    try:
        with open(PATH) as f:
            d = json.load(f)
    except Exception as e:
        print("FAIL: cannot parse JSON (%s)" % e)
        return 1

    # 2. _meta source + license
    meta = d.get("_meta", {})
    check("_meta present", "_meta missing")
    check(bool(meta.get("source")), "_meta.source missing")
    check(bool(meta.get("license")), "_meta.license missing")

    centers = d.get("centers", [])
    channels = d.get("channels", [])
    gates = d.get("gates", [])

    # 3. counts
    check(len(centers) == 9, f"center count {len(centers)} != 9")
    check(len(channels) == 36, f"channel count {len(channels)} != 36")
    check(len(gates) == 64, f"gate count {len(gates)} != 64")

    center_ids = {c["id"] for c in centers}
    center_name_by_id = {c["id"]: c["name"] for c in centers}

    # 5. gate numbers 1..64 each exactly once
    gate_numbers = [g["number"] for g in gates]
    check(sorted(gate_numbers) == list(range(1, 65)),
          f"gate numbers not exactly 1..64 (missing/dup). n={len(gate_numbers)} unique={len(set(gate_numbers))}")
    # every gate's center references a real center
    bad_gate_center = [g["number"] for g in gates if g.get("center") not in center_ids]
    check(not bad_gate_center, f"gates with unknown center id: {bad_gate_center[:10]}")

    # build gate -> center from the gates list (source of truth for assignment)
    gate_to_center = {g["number"]: g["center"] for g in gates}

    # 4. every channel's gates belong to its two centers
    bad_ch = []
    for ch in channels:
        a, b = ch["gates"]
        cp = set(ch["center_pair"])
        ca = gate_to_center.get(a)
        cb = gate_to_center.get(b)
        if ca not in cp or cb not in cp:
            bad_ch.append((ch["id"], a, b, sorted(cp), [ca, cb]))
    check(not bad_ch, f"{len(bad_ch)} channel(s) whose gates don't map to their center_pair: {bad_ch[:5]}")

    # channel center-pairs reference real centers
    bad_ref = [ch["id"] for ch in channels for c in ch["center_pair"] if c not in center_ids]
    check(not bad_ref, f"channel center_pair references unknown center ids: {bad_ref[:10]}")

    # 6. per-center gate tally sums to 64
    tally = {cid: 0 for cid in center_ids}
    for g in gates:
        if g["center"] in tally:
            tally[g["center"]] += 1
    check(sum(tally.values()) == 64, f"per-center gate tally {sum(tally.values())} != 64")

    # report
    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        print(f"counts: centers={len(centers)} channels={len(channels)} gates={len(gates)}")
        return 1
    print("PASS")
    print(f"counts: centers={len(centers)} channels={len(channels)} gates={len(gates)}")
    print("per-center gates:")
    for cid in sorted(tally):
        print(f"  {center_name_by_id[cid]:<12} {tally[cid]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
