#!/usr/bin/env python3
"""
===============================================================================
EAGLE CAD Agentic Visualization & Rendering Bridge (visualize.py)
===============================================================================
Author: Francisco Betancourt & Antigravity (Sam)
Description:
    Agentic bridge script for EAGLE CAD Skill that integrates with the standalone
    'eagle-viewer' application. Allows agents to generate interactive HTML
    visualizers, export vector SVGs, and inspect circuit topologies.
"""

import sys
import os
import json
import shutil
import argparse
import subprocess
from pathlib import Path


def find_eagle_viewer_bin() -> str:
    """Locates the eagle-viewer executable or Python entrypoint."""
    # 1. Check system PATH
    bin_path = shutil.which("eagle-viewer")
    if bin_path and os.path.exists(bin_path):
        return bin_path

    # 2. Check user local bin
    user_bin = os.path.expanduser("~/.local/bin/eagle-viewer")
    if os.path.exists(user_bin):
        return user_bin

    # 3. Check Gemini workspace standalone project
    workspace_app = os.path.expanduser("~/Gemini/eagle_viewer_py/main.py")
    if os.path.exists(workspace_app):
        return workspace_app

    return ""


def print_schema():
    schema = {
        "status": "str ('success' | 'error')",
        "circuit_name": "str",
        "html_viewer": "str (path to generated interactive HTML file)",
        "svg_schematic": "str (path to exported schematic SVG, if requested)",
        "svg_board_top": "str (path to isolated Top layer SVG)",
        "svg_board_bottom": "str (path to isolated Bottom layer mirrored SVG)",
        "svg_board_both": "str (path to combined PCB board SVG)",
        "png_schematic": "str (path to exported schematic PNG, if requested)",
        "png_board_top": "str (path to isolated Top layer PNG)",
        "png_board_bottom": "str (path to isolated Bottom layer mirrored PNG)",
        "png_board_both": "str (path to combined PCB board PNG)",
        "browser_opened": "bool",
        "cli_used": "str (executable path)"
    }
    print(json.dumps(schema, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="EAGLE CAD Skill Visualization & SVG Rendering Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Open interactive web viewer:
  python3 visualize.py circuit.sch circuit.brd

  # Generate standalone HTML silently without browser:
  python3 visualize.py circuit.brd --no-open -o /tmp/viewer.html

  # Export vector SVGs for schematic and PCB:
  python3 visualize.py circuit.brd --export-svg ./svgs/ --no-open

  # Inspect JSON output schema:
  python3 visualize.py --schema
"""
    )

    parser.add_argument("files", nargs="*", help="EAGLE .sch / .brd file paths or circuit base name")
    parser.add_argument("--sch", type=str, default=None, help="Explicit path to schematic (.sch)")
    parser.add_argument("--brd", type=str, default=None, help="Explicit path to board (.brd)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output HTML file path")
    parser.add_argument("--export-svg", nargs="?", const=".", default=None, metavar="DIR", help="Export SVG directory")
    parser.add_argument("--export-png", nargs="?", const=".", default=None, metavar="DIR", help="Export PNG preview directory (ideal for Antigravity artifacts)")
    parser.add_argument("--no-open", action="store_true", help="Do not open default web browser")
    parser.add_argument("--theme", choices=["dark", "classic"], default="dark", help="Viewer theme")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON result for agent consumption")
    parser.add_argument("--schema", action="store_true", help="Print script output JSON schema")

    args = parser.parse_args()

    if args.schema:
        print_schema()
        sys.exit(0)

    viewer_bin = find_eagle_viewer_bin()
    if not viewer_bin:
        err = {
            "status": "error",
            "message": "eagle-viewer executable not found. Ensure ~/Gemini/eagle_viewer_py is present or ~/.local/bin/eagle-viewer exists."
        }
        if args.json:
            print(json.dumps(err, indent=2))
        else:
            print(f"Error: {err['message']}", file=sys.stderr)
        sys.exit(1)

    # Build command invocation
    if viewer_bin.endswith(".py"):
        cmd = [sys.executable, viewer_bin]
    else:
        cmd = [viewer_bin]

    for f in args.files:
        cmd.append(f)

    if args.sch:
        cmd.extend(["--sch", args.sch])
    if args.brd:
        cmd.extend(["--brd", args.brd])
    if args.output:
        cmd.extend(["-o", args.output])
    if args.export_svg is not None:
        cmd.extend(["--export-svg", args.export_svg])
    if args.export_png is not None:
        cmd.extend(["--export-png", args.export_png])
    if args.no_open:
        cmd.append("--no-open")
    if args.theme:
        cmd.extend(["--theme", args.theme])

    # Run the standalone viewer CLI
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        err = {
            "status": "error",
            "message": proc.stderr.strip() or proc.stdout.strip(),
            "command": " ".join(cmd)
        }
        if args.json:
            print(json.dumps(err, indent=2))
        else:
            print(f"Error executing eagle-viewer:\n{err['message']}", file=sys.stderr)
        sys.exit(proc.returncode)

    # Determine paths generated
    circuit_name = "eagle_design"
    for f in args.files + [args.brd, args.sch]:
        if f:
            circuit_name = os.path.splitext(os.path.basename(f))[0]
            break

    target_html = args.output or os.path.abspath(f"{circuit_name}_viewer.html")
    svg_dir = os.path.abspath(args.export_svg) if args.export_svg else None

    result = {
        "status": "success",
        "circuit_name": circuit_name,
        "html_viewer": target_html if os.path.exists(target_html) else None,
        "svg_schematic": None,
        "svg_board_top": None,
        "svg_board_bottom": None,
        "svg_board_both": None,
        "png_schematic": None,
        "png_board_top": None,
        "png_board_bottom": None,
        "png_board_both": None,
        "browser_opened": not args.no_open,
        "cli_used": viewer_bin
    }

    if svg_dir:
        for key, suffix in [
            ("svg_schematic", "_schematic.svg"),
            ("svg_board_top", "_board_top.svg"),
            ("svg_board_bottom", "_board_bottom.svg"),
            ("svg_board_both", "_board.svg"),
        ]:
            p = os.path.join(svg_dir, f"{circuit_name}{suffix}")
            if os.path.exists(p):
                result[key] = p

    png_dir = os.path.abspath(args.export_png) if args.export_png else None
    if png_dir:
        for key, suffix in [
            ("png_schematic", "_schematic.png"),
            ("png_board_top", "_board_top.png"),
            ("png_board_bottom", "_board_bottom.png"),
            ("png_board_both", "_board.png"),
        ]:
            p = os.path.join(png_dir, f"{circuit_name}{suffix}")
            if os.path.exists(p):
                result[key] = p

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(proc.stdout.strip())
        print(f"\n[Agentic Bridge Summary]")
        print(f"  Status:         {result['status']}")
        print(f"  Circuit:        {result['circuit_name']}")
        print(f"  HTML Viewer:    {result['html_viewer']}")
        if result['svg_schematic']:
            print(f"  Schematic SVG:  {result['svg_schematic']}")
        if result['svg_board']:
            print(f"  Board SVG:      {result['svg_board']}")


if __name__ == "__main__":
    main()
