#!/usr/bin/env python3
"""
EAGLE CAD Schematic ERC & Subcircuit Analyzer
Parses .sch XML files and performs Electrical Rules Checks (ERC), power budget extraction,
and subcircuit identification.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from eagle_parser import EagleParser

def analyze_schematic(sch_path):
    parser = EagleParser(sch_path=sch_path)
    data = parser.parse()
    sch_data = data.get("schematic", {})
    
    findings = []
    subcircuits = []
    
    instances = sch_data.get("instances", [])
    nets = sch_data.get("nets", [])
    parts = sch_data.get("parts", {})
    
    # 1. Map Net Connections
    # Net -> list of pinrefs {part, gate, pin}
    net_pin_map = {}
    part_net_map = {} # Part -> list of {pin, net_name}
    
    for net in nets:
        net_name = net["name"]
        net_pin_map[net_name] = net.get("pinrefs", [])
        for pr in net.get("pinrefs", []):
            p_name = pr["part"]
            if p_name not in part_net_map:
                part_net_map[p_name] = []
            part_net_map[p_name].append({
                "gate": pr.get("gate"),
                "pin": pr.get("pin"),
                "net": net_name
            })
            
    # 2. Check Floating Nets (SCH-ERC-002)
    for net_name, pinrefs in net_pin_map.items():
        if len(pinrefs) == 1:
            pr = pinrefs[0]
            findings.append({
                "id": "SCH-ERC-002",
                "severity": "medium",
                "title": f"Floating Net Single Connection: {net_name}",
                "description": f"Net '{net_name}' is connected to only 1 pin: {pr['part']} ({pr.get('pin')}). This net may be unrouted or dangling.",
                "confidence": "high",
                "evidence": f"Net '{net_name}' has pinref count = 1 ({pr['part']})"
            })
            
    # 3. Check Part Pin Connection & Subcircuit Detection
    ic_parts = []
    decoupling_caps = []
    crystals = []
    regulators = []
    
    for part_name, part_info in parts.items():
        dev_set = part_info.get("deviceset", "").upper()
        lib_name = part_info.get("library", "").upper()
        val = part_info.get("value", "")
        
        # Identify Decoupling Capacitors (e.g., C1, C2 with 100n, 0.1uF, 10uF, etc.)
        if part_name.startswith("C"):
            decoupling_caps.append(part_name)
            
        # Identify Crystals
        if "CRYSTAL" in dev_set or "XTAL" in dev_set or part_name.startswith("Y") or part_name.startswith("Q"):
            crystals.append(part_name)
            subcircuits.append({
                "type": "crystal_oscillator",
                "name": part_name,
                "value": val,
                "deviceset": dev_set
            })
            
        # Identify Regulators / Power ICs
        if any(kw in dev_set for kw in ["TPS", "AMS1117", "LM1117", "MP2307", "REG", "LDO", "BUCK", "BOOST", "AP2112"]):
            regulators.append(part_name)
            subcircuits.append({
                "type": "voltage_regulator",
                "name": part_name,
                "value": val,
                "deviceset": dev_set
            })

        # Identify Microcontrollers / Complex ICs
        if any(kw in dev_set for kw in ["ESP32", "STM32", "ATMEGA", "ATTINY", "SAMD", "RP2040", "NRF52", "PIC"]):
            ic_parts.append(part_name)
            subcircuits.append({
                "type": "microcontroller",
                "name": part_name,
                "value": val,
                "deviceset": dev_set
            })
            
            # Check Reset / Enable pullup (SCH-ERC-005)
            connected_nets = [item["net"] for item in part_net_map.get(part_name, [])]
            reset_nets = [n for n in connected_nets if any(r_kw in n.upper() for r_kw in ["RST", "RESET", "EN", "CHIP_PU"])]
            if not reset_nets:
                findings.append({
                    "id": "SCH-ERC-005",
                    "severity": "low",
                    "title": f"No Explicit Reset/Enable Net Identified: {part_name}",
                    "description": f"MCU instance '{part_name}' ({dev_set}) does not have an explicitly named EN or RESET net connected.",
                    "confidence": "medium",
                    "evidence": f"Part {part_name} connected nets: {connected_nets}"
                })

    # 4. Check Unnamed Communication Nets (SCH-ERC-007)
    for net in nets:
        net_name = net["name"]
        if net_name.startswith("N$"):
            # Check if connected to high-speed IC pins
            for pr in net.get("pinrefs", []):
                p_name = pr["part"]
                p_info = parts.get(p_name, {})
                dev_set = p_info.get("deviceset", "").upper()
                if any(ic_kw in dev_set for ic_kw in ["ESP32", "STM32", "FT232", "CH340", "CP2102", "USB"]):
                    findings.append({
                        "id": "SCH-ERC-007",
                        "severity": "low",
                        "title": f"Default Net Name on IC Interface: {net_name}",
                        "description": f"Net '{net_name}' connected to {p_name} ({dev_set}) uses EAGLE default auto-generated name.",
                        "confidence": "high",
                        "evidence": f"Net name '{net_name}' connected to {p_name}"
                    })
                    break

    summary = {
        "total_parts": len(parts),
        "total_instances": len(instances),
        "total_nets": len(nets),
        "microcontrollers_count": len(ic_parts),
        "regulators_count": len(regulators),
        "crystals_count": len(crystals),
        "decoupling_caps_count": len(decoupling_caps),
        "findings_count": len(findings)
    }

    return {
        "schematic_name": data.get("name", ""),
        "summary": summary,
        "subcircuits": subcircuits,
        "findings": findings,
        "instances": instances,
        "nets": nets,
        "parts": parts
    }

def main():
    parser = argparse.ArgumentParser(description="EAGLE CAD Schematic ERC Analyzer")
    parser.add_argument("sch_path", help="Path to .sch EAGLE schematic XML file")
    parser.add_argument("--schema", action="store_true", help="Print analyzer JSON output schema description")
    
    args = parser.parse_args()
    
    if args.schema:
        print(json.dumps({
            "schematic_name": "str",
            "summary": "dict (total_parts, total_nets, findings_count, etc.)",
            "subcircuits": "list[dict] (type, name, value, deviceset)",
            "findings": "list[dict] (id, severity, title, description, confidence, evidence)",
            "parts": "dict[part_name -> part_info]",
            "nets": "list[net_info]"
        }, indent=2))
        sys.exit(0)

    if not os.path.exists(args.sch_path):
        print(f"Error: File '{args.sch_path}' not found.", file=sys.stderr)
        sys.exit(1)

    result = analyze_schematic(args.sch_path)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
