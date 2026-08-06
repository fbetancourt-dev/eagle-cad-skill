#!/usr/bin/env python3
"""
EAGLE CAD Bill of Materials (BOM) Extractor
Extracts component lists, quantities, values, footprints, and MPNs from EAGLE .sch and .brd files.
"""

import sys
import os
import json
import csv
import argparse
from eagle_parser import EagleParser

def export_bom(sch_path=None, brd_path=None):
    parser = EagleParser(sch_path=sch_path, brd_path=brd_path)
    data = parser.parse()
    
    parts = data["schematic"].get("parts", {})
    elements = {elem["name"]: elem for elem in data["board"].get("elements", [])}
    
    bom_dict = {} # Key: (deviceset, value, package) -> {count, designators, deviceset, value, package, library}
    
    all_designators = sorted(set(list(parts.keys()) + list(elements.keys())))
    
    for des in all_designators:
        p_info = parts.get(des, {})
        e_info = elements.get(des, {})
        
        ds_name = p_info.get("deviceset") or e_info.get("library", "Unknown")
        val = p_info.get("value") or e_info.get("value", "")
        pkg = e_info.get("package") or p_info.get("device", "")
        lib = p_info.get("library") or e_info.get("library", "")
        
        group_key = (ds_name, val, pkg, lib)
        if group_key not in bom_dict:
            bom_dict[group_key] = {
                "deviceset": ds_name,
                "value": val,
                "package": pkg,
                "library": lib,
                "quantity": 0,
                "designators": []
            }
            
        bom_dict[group_key]["quantity"] += 1
        bom_dict[group_key]["designators"].append(des)
        
    bom_items = list(bom_dict.values())
    bom_items.sort(key=lambda x: x["designators"][0])
    
    return bom_items

def main():
    parser = argparse.ArgumentParser(description="EAGLE CAD Bill of Materials (BOM) Extractor")
    parser.add_argument("--sch", help="Path to .sch EAGLE schematic file")
    parser.add_argument("--brd", help="Path to .brd EAGLE board file")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format (json or csv)")
    
    args = parser.parse_args()
    
    if not args.sch and not args.brd:
        print("Error: Specify at least --sch or --brd file.", file=sys.stderr)
        sys.exit(1)

    bom = export_bom(sch_path=args.sch, brd_path=args.brd)
    
    if args.format == "json":
        print(json.dumps(bom, indent=2))
    elif args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(["Item", "Quantity", "Designators", "Value", "DeviceSet", "Package", "Library"])
        for idx, item in enumerate(bom, start=1):
            writer.writerow([
                idx,
                item["quantity"],
                ", ".join(item["designators"]),
                item["value"],
                item["deviceset"],
                item["package"],
                item["library"]
            ])

if __name__ == "__main__":
    main()
