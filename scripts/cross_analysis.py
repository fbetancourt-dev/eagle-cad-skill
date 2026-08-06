#!/usr/bin/env python3
"""
EAGLE CAD Cross-Analysis Engine (Schematic vs. Board)
Cross-verifies schematic instance parts and nets against PCB elements and routed signals.
"""

import sys
import os
import json
import argparse
from eagle_parser import EagleParser
from analyze_schematic import analyze_schematic
from analyze_pcb import analyze_pcb

def cross_analyze(sch_path, brd_path):
    sch_res = analyze_schematic(sch_path)
    brd_res = analyze_pcb(brd_path)
    
    findings = []
    
    sch_parts = sch_res.get("parts", {})
    brd_elements = {elem["name"]: elem for elem in brd_res.get("elements", [])}
    
    sch_nets = {net["name"]: net for net in sch_res.get("nets", [])}
    brd_signals = {sig["name"]: sig for sig in brd_res.get("signals", [])}
    
    # 1. Check Schematic Parts vs Board Elements (CROSS-001)
    missing_on_board = []
    value_mismatches = []
    
    for p_name, p_info in sch_parts.items():
        if p_name not in brd_elements:
            missing_on_board.append(p_name)
            findings.append({
                "id": "CROSS-001",
                "severity": "high",
                "title": f"Schematic Part Missing on PCB: {p_name}",
                "description": f"Part '{p_name}' ({p_info.get('deviceset')}) exists in schematic but is not placed on the PCB layout.",
                "confidence": "high",
                "evidence": f"Part {p_name} in .sch parts dictionary but not in .brd elements"
            })
        else:
            brd_elem = brd_elements[p_name]
            sch_val = p_info.get("value", "")
            brd_val = brd_elem.get("value", "")
            if sch_val and brd_val and sch_val != brd_val:
                value_mismatches.append((p_name, sch_val, brd_val))
                findings.append({
                    "id": "CROSS-002",
                    "severity": "medium",
                    "title": f"Component Value Mismatch: {p_name}",
                    "description": f"Part '{p_name}' schematic value '{sch_val}' differs from board value '{brd_val}'.",
                    "confidence": "high",
                    "evidence": f"Schematic value = '{sch_val}', Board value = '{brd_val}'"
                })

    # 2. Check Schematic Nets vs Board Signals (CROSS-003)
    missing_signals = []
    for net_name in sch_nets:
        if net_name not in brd_signals:
            # Ignore standard single pin internal nets if desired, but report unmapped nets
            missing_signals.append(net_name)
            findings.append({
                "id": "CROSS-003",
                "severity": "medium",
                "title": f"Schematic Net Missing from PCB Signals: {net_name}",
                "description": f"Net '{net_name}' defined in schematic does not exist in board signal list.",
                "confidence": "high",
                "evidence": f"Net '{net_name}' present in .sch nets but missing in .brd signals"
            })

    summary = {
        "schematic_parts_count": len(sch_parts),
        "board_elements_count": len(brd_elements),
        "schematic_nets_count": len(sch_nets),
        "board_signals_count": len(brd_signals),
        "missing_on_board_count": len(missing_on_board),
        "value_mismatches_count": len(value_mismatches),
        "missing_signals_count": len(missing_signals),
        "findings_count": len(findings)
    }

    return {
        "project_name": sch_res.get("schematic_name", ""),
        "summary": summary,
        "findings": findings,
        "schematic_summary": sch_res.get("summary"),
        "board_summary": brd_res.get("summary")
    }

def main():
    parser = argparse.ArgumentParser(description="EAGLE CAD Cross-Analysis Engine (Schematic vs. Board)")
    parser.add_argument("sch_path", help="Path to .sch EAGLE schematic XML file")
    parser.add_argument("brd_path", help="Path to .brd EAGLE board XML file")
    parser.add_argument("--schema", action="store_true", help="Print analyzer JSON output schema description")
    
    args = parser.parse_args()
    
    if args.schema:
        print(json.dumps({
            "project_name": "str",
            "summary": "dict (missing_on_board_count, value_mismatches_count, etc.)",
            "findings": "list[dict] (id, severity, title, description, confidence, evidence)",
            "schematic_summary": "dict",
            "board_summary": "dict"
        }, indent=2))
        sys.exit(0)

    if not os.path.exists(args.sch_path):
        print(f"Error: File '{args.sch_path}' not found.", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(args.brd_path):
        print(f"Error: File '{args.brd_path}' not found.", file=sys.stderr)
        sys.exit(1)

    result = cross_analyze(args.sch_path, args.brd_path)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
