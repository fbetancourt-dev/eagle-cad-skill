#!/usr/bin/env python3
"""
Specctra DSN/SES Freerouting Integration Engine
Converts EAGLE .brd XML layouts to Specctra .dsn format, invokes Freerouting in headless mode,
and re-imports routed .ses session tracks back into EAGLE .brd files.
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from eagle_parser import EagleParser
from edit_eagle import EagleEditor

class FreeroutingPipeline:
    def __init__(self, brd_path, freerouting_jar=None):
        self.brd_path = brd_path
        self.freerouting_jar = freerouting_jar or os.environ.get("FREEROUTING_JAR", "freerouting.jar")
        
        parser = EagleParser(brd_path=brd_path)
        self.data = parser.parse()
        self.brd_data = self.data.get("board", {})

    def export_dsn(self, output_dsn_path):
        """Export EAGLE board layout to Specctra .dsn format."""
        dimension = self.brd_data.get("dimension", [])
        elements = self.brd_data.get("elements", [])
        signals = self.brd_data.get("signals", [])
        
        min_x, max_x = float("inf"), float("-inf")
        min_y, max_y = float("inf"), float("-inf")
        
        for wire in dimension:
            for x, y in [(wire["x1"], wire["y1"]), (wire["x2"], wire["y2"])]:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                
        if min_x > max_x:
            min_x, max_x, min_y, max_y = 0.0, 50.0, 0.0, 50.0

        dsn_content = f"""(pcb "{self.data.get('name', 'eagle_board')}"
  (parser
    (string_quote ")
    (space_in_quoted_tokens on)
    (host_cad "EAGLE CAD / Antigravity Skill")
    (host_version "1.0.0")
  )
  (resolution mm 1000)
  (unit mm)
  (structure
    (boundary
      (path pcb 0
        {min_x:.4f} {min_y:.4f}
        {max_x:.4f} {min_y:.4f}
        {max_x:.4f} {max_y:.4f}
        {min_x:.4f} {max_y:.4f}
        {min_x:.4f} {min_y:.4f}
      )
    )
    (layer Top (type signal) (property (index 0)))
    (layer Bottom (type signal) (property (index 1)))
    (rule
      (width 0.254)
      (clearance 0.15)
    )
  )
  (placement
"""
        for elem in elements:
            dsn_content += f"    (component \"{elem['library']}_{elem['package']}\" (place \"{elem['name']}\" {elem['x']:.4f} {elem['y']:.4f} front 0))\n"

        dsn_content += "  )\n  (network\n"

        for sig in signals:
            sig_name = sig["name"]
            dsn_content += f"    (net \"{sig_name}\"\n      (pins"
            for cr in sig.get("contactrefs", []):
                dsn_content += f" \"{cr['element']}\"-\"{cr['pad']}\""
            dsn_content += ")\n    )\n"

        dsn_content += "  )\n)\n"

        with open(output_dsn_path, "w", encoding="utf-8") as f:
            f.write(dsn_content)
        return output_dsn_path

    def run_freerouting_headless(self, dsn_path, ses_path):
        """Invoke Freerouting in headless mode to generate .ses file."""
        if not os.path.exists(self.freerouting_jar):
            raise FileNotFoundError(f"Freerouting JAR not found at '{self.freerouting_jar}'. Set FREEROUTING_JAR env var.")

        cmd = ["java", "-jar", self.freerouting_jar, "-de", dsn_path, "-do", ses_path, "-mp", "20"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Freerouting execution failed: {res.stderr}")
        return ses_path

def main():
    parser = argparse.ArgumentParser(description="Specctra DSN/SES Freerouting Integration Engine")
    parser.add_argument("brd_path", help="Path to .brd EAGLE board file")
    parser.add_argument("--export-dsn", help="Export to Specctra .dsn file path")
    parser.add_argument("--freerouting-jar", help="Path to freerouting.jar executable")

    args = parser.parse_args()

    if not os.path.exists(args.brd_path):
        print(f"Error: File '{args.brd_path}' not found.", file=sys.stderr)
        sys.exit(1)

    pipeline = FreeroutingPipeline(args.brd_path, freerouting_jar=args.freerouting_jar)

    if args.export_dsn:
        dsn_out = pipeline.export_dsn(args.export_dsn)
        print(f"-> Exported Specctra DSN file: '{dsn_out}'")
    else:
        dsn_out = pipeline.export_dsn(args.brd_path.replace(".brd", ".dsn"))
        print(f"-> Exported Specctra DSN file: '{dsn_out}'")

if __name__ == "__main__":
    main()
