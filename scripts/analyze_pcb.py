#!/usr/bin/env python3
"""
EAGLE CAD PCB DRC & DFM Analyzer
Parses .brd XML files and performs Design Rules Check (DRC), track width verification,
via drill inspection, and clearance analysis.
"""

import sys
import os
import json
import math
import argparse
from pathlib import Path
from eagle_parser import EagleParser

def analyze_pcb(brd_path):
    parser = EagleParser(brd_path=brd_path)
    data = parser.parse()
    brd_data = data.get("board", {})
    
    findings = []
    
    elements = brd_data.get("elements", [])
    signals = brd_data.get("signals", [])
    packages = brd_data.get("packages", {})
    dimension = brd_data.get("dimension", [])
    holes = brd_data.get("holes", [])
    
    # 1. Calculate Board Outline Bounds (Layer 20 Dimension)
    min_x, max_x = float("inf"), float("-inf")
    min_y, max_y = float("inf"), float("-inf")
    
    for wire in dimension:
        for x, y in [(wire["x1"], wire["y1"]), (wire["x2"], wire["y2"])]:
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y
            
    board_width = max_x - min_x if max_x > min_x else 0.0
    board_height = max_y - min_y if max_y > min_y else 0.0
    board_area_cm2 = (board_width * board_height) / 100.0 if board_width > 0 else 0.0
    
    # 2. Inspect Signals, Track Widths, and Via Drills (PCB-DRC-001, PCB-DRC-002)
    thin_traces = []
    small_vias = []
    unrouted_signals = []
    
    MIN_TRACE_WIDTH_MM = 0.15  # 6 mil standard limit
    MIN_VIA_DRILL_MM = 0.3     # 12 mil standard drill limit
    
    for sig in signals:
        sig_name = sig["name"]
        wires = sig.get("wires", [])
        vias = sig.get("vias", [])
        contactrefs = sig.get("contactrefs", [])
        
        # Check if signal has contactrefs but no physical wires or polygons
        if len(contactrefs) > 1 and len(wires) == 0 and len(sig.get("polygons", [])) == 0:
            unrouted_signals.append(sig_name)
            findings.append({
                "id": "PCB-DRC-003",
                "severity": "high",
                "title": f"Unrouted Signal / Airwire Detected: {sig_name}",
                "description": f"Signal '{sig_name}' connects {len(contactrefs)} pads but has zero routed wires or copper polygons.",
                "confidence": "high",
                "evidence": f"Signal '{sig_name}' contactrefs = {len(contactrefs)}, wires = 0"
            })

        for w in wires:
            w_width = w.get("width", 0.254)
            if 0.0 < w_width < MIN_TRACE_WIDTH_MM:
                thin_traces.append((sig_name, w_width))
                findings.append({
                    "id": "PCB-DRC-001",
                    "severity": "medium",
                    "title": f"Thin Trace Width (< {MIN_TRACE_WIDTH_MM}mm): {sig_name}",
                    "description": f"Signal '{sig_name}' contains trace width of {w_width:.3f} mm, below standard {MIN_TRACE_WIDTH_MM} mm fab limit.",
                    "confidence": "high",
                    "evidence": f"Wire in signal {sig_name} has width = {w_width:.3f} mm"
                })
                break

        for v in vias:
            v_drill = v.get("drill", 0.5)
            v_dia = v.get("diameter", 0.8)
            if 0.0 < v_drill < MIN_VIA_DRILL_MM:
                small_vias.append((sig_name, v_drill))
                findings.append({
                    "id": "PCB-DRC-002",
                    "severity": "medium",
                    "title": f"Small Via Drill Size (< {MIN_VIA_DRILL_MM}mm): {sig_name}",
                    "description": f"Signal '{sig_name}' has via drill diameter of {v_drill:.3f} mm, below standard fab capability.",
                    "confidence": "high",
                    "evidence": f"Via at ({v['x']}, {v['y']}) has drill = {v_drill:.3f} mm"
                })
                break

    # 3. Check Component Placements near Edge (PCB-DRC-006)
    EDGE_MARGIN_MM = 0.5
    if board_width > 0 and board_height > 0:
        for elem in elements:
            e_name = elem["name"]
            ex, ey = elem["x"], elem["y"]
            dist_left = ex - min_x
            dist_right = max_x - ex
            dist_bottom = ey - min_y
            dist_top = max_y - ey
            min_dist = min(dist_left, dist_right, dist_bottom, dist_top)
            
            if min_dist < EDGE_MARGIN_MM:
                findings.append({
                    "id": "PCB-DRC-006",
                    "severity": "low",
                    "title": f"Component Near Board Edge: {e_name}",
                    "description": f"Element '{e_name}' is placed {min_dist:.2f} mm from the board edge outline.",
                    "confidence": "medium",
                    "evidence": f"Element {e_name} coords ({ex}, {ey}) near outline [{min_x}, {max_x}, {min_y}, {max_y}]"
                })

    summary = {
        "board_width_mm": round(board_width, 2),
        "board_height_mm": round(board_height, 2),
        "board_area_cm2": round(board_area_cm2, 2),
        "total_elements": len(elements),
        "total_signals": len(signals),
        "total_holes": len(holes),
        "unrouted_signals_count": len(unrouted_signals),
        "thin_traces_count": len(thin_traces),
        "small_vias_count": len(small_vias),
        "findings_count": len(findings)
    }

    return {
        "board_name": data.get("name", ""),
        "summary": summary,
        "findings": findings,
        "elements": elements,
        "signals": signals,
        "holes": holes
    }

def main():
    parser = argparse.ArgumentParser(description="EAGLE CAD PCB DRC & DFM Analyzer")
    parser.add_argument("brd_path", help="Path to .brd EAGLE board XML file")
    parser.add_argument("--schema", action="store_true", help="Print analyzer JSON output schema description")
    
    args = parser.parse_args()
    
    if args.schema:
        print(json.dumps({
            "board_name": "str",
            "summary": "dict (board_width_mm, board_height_mm, total_elements, total_signals, etc.)",
            "findings": "list[dict] (id, severity, title, description, confidence, evidence)",
            "elements": "list[dict] (name, library, package, value, x, y, rot)",
            "signals": "list[dict] (name, wires, vias, contactrefs, polygons)",
            "holes": "list[dict] (x, y, drill)"
        }, indent=2))
        sys.exit(0)

    if not os.path.exists(args.brd_path):
        print(f"Error: File '{args.brd_path}' not found.", file=sys.stderr)
        sys.exit(1)

    result = analyze_pcb(args.brd_path)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
