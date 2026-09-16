---
name: eagle
description: >-
  Analyze, edit, autoroute, visualize, and automate Autodesk and CadSoft EAGLE CAD schematic (.sch) and board layout (.brd) XML files,
  as well as EAGLE script (.scr) files and libraries (.lbr). Performs Electrical Rules Check (ERC),
  Design Rules Check (DRC), Design for Manufacturing (DFM) audits, schematic-vs-PCB cross-analysis,
  BOM extraction, dual-mode hybrid PCB autorouting (Native Python A* + Freerouting DSN/SES),
  interactive web visualizer rendering and SVG vector export via standalone eagle-viewer,
  XML editing/serialization, and EAGLE GUI automation script generation.
  Supports integration with datasheets, bom, emc, and spice skills. Use whenever the user mentions
  .sch, .brd, .scr, autoroute, visualize, EAGLE CAD, CadSoft, EAGLE project, EAGLE schematic, EAGLE board, or requests a design review/editing/autorouting/visualization
  for EAGLE CAD files.
---

# EAGLE CAD Project Analysis, Autorouting, Visualization & Automation Skill

## Related Skills

| Skill | Purpose |
|-------|---------|
| `bom` | BOM extraction, enrichment, pricing, and distributor export |
| `datasheets` | Extract structured specs from component PDFs for pin-level verification |
| `digikey` / `mouser` / `lcsc` / `element14` | Search electronics distributors and download component datasheets |
| `jlcpcb` / `pcbway` | PCB fabrication and assembly design rules & ordering |
| `spice` | Circuit simulation of detected analog subcircuits |
| `emc` | Pre-compliance EMC risk analysis |

## Entry-Point Scripts

### Analysis & Inspection
- `python3 <skill-path>/scripts/analyze_schematic.py <file.sch>` — Parses schematic XML, extracts instances, nets, subcircuits, and runs ERC checks.
- `python3 <skill-path>/scripts/analyze_pcb.py <file.brd>` — Parses board XML, calculates dimensions, checks trace widths, via drills, and unrouted airwires.
- `python3 <skill-path>/scripts/cross_analysis.py <file.sch> <file.brd>` — Cross-verifies schematic parts/nets against board elements/signals.
- `python3 <skill-path>/scripts/export_bom.py --sch <file.sch> --brd <file.brd>` — Exports structured BOM JSON/CSV.

### Dual-Engine Hybrid Autorouting
- `python3 <skill-path>/scripts/autoroute.py <file.brd> --mode auto` — Hybrid multi-tier mode: runs native pure Python A* grid search first; falls back to Specctra DSN/SES Freerouting engine if needed.
- `python3 <skill-path>/scripts/autoroute_astar.py <file.brd> --grid-step 0.5` — Pure Python native 2D/3D grid pathfinder with via/corner cost penalties.
- `python3 <skill-path>/scripts/autoroute_freerouting.py <file.brd> --export-dsn output.dsn` — Specctra DSN/SES exporter & Freerouting engine integration.

### Visualization & Rendering (Standalone `eagle-viewer` Bridge)
- `python3 <skill-path>/scripts/visualize.py <file.sch> <file.brd>` — Generates and launches interactive web visualizer in default browser.
- `python3 <skill-path>/scripts/visualize.py <file.brd> --no-open -o /path/to/viewer.html` — Generates self-contained interactive HTML silently (ideal for reports).
- `python3 <skill-path>/scripts/visualize.py <file.brd> --export-svg ./svgs/ --no-open` — Exports standalone vector SVGs for schematic and PCB to embed directly in artifacts.
- `python3 <skill-path>/scripts/visualize.py <file.brd> --json` — Emits structured JSON metadata for agent workflow automation.

### Editing & Automation
- `python3 <skill-path>/scripts/edit_eagle.py <file.sch|brd> --set-value R1 10k --rename-net GND AGND --set-attr R1 MPN PT0603` — Programmatically edits components, attributes, and net names, re-serializing clean EAGLE XML.
- `python3 <skill-path>/scripts/generate_scr.py -o <file.scr> --add-component C-US@adafruit C1 10 20` — Compiles executable EAGLE batch scripts (`.scr`) for GUI automation.
- **Native Autodesk EAGLE 7.7.0 Integration:**
  - Headless batch export: `eagle -N- -C "SCRIPT top.scr; EXPORT IMAGE 'top.png' 300; QUIT;" <file.brd>` (always pass `-N-` to suppress modal prompts).
  - Layer isolation scripts in `~/Applications/eagle-7.7.0/scr/`: `top.scr`, `bottom.scr`, `both.scr`, `all.scr`.
  - Board editor keyboard shortcuts registered in `eagle.scr`: `Ctrl+T` (Top), `Ctrl+B` (Bottom), `Ctrl+A` (Both), `Ctrl+Shift+A` (All).
  - Desktop DOM handling via `dogtail-gui-accessibility` for unhandled GUI modal dialogs.

Use `--schema` flag on any script to inspect its output structure:
```bash
python3 <skill-path>/scripts/analyze_schematic.py --schema
python3 <skill-path>/scripts/analyze_pcb.py --schema
python3 <skill-path>/scripts/cross_analysis.py --schema
python3 <skill-path>/scripts/visualize.py --schema
```

## Minimum Review Checklist

For a full EAGLE CAD design review, run all applicable analysis scripts and account for each item below:

1. **Schematic Analysis (`analyze_schematic.py`):** Identify parts, instances, nets, power domains, decoupling caps, and floating nets.
2. **PCB Layout Analysis (`analyze_pcb.py`):** Calculate board area, check minimum trace width, via drills, edge clearances, and airwires.
3. **Cross-Analysis (`cross_analysis.py`):** Check for missing schematic parts on board layout, value mismatches, and unrouted signals.
4. **Hybrid Autorouting (`autoroute.py`):** Solve remaining unrouted airwire signals using native A* pathfinding or Freerouting engine.
5. **Visual Inspection & Rendering (`visualize.py`):** Generate interactive web visualizer and export vector SVGs for artifact embedding.
6. **BOM Extraction (`export_bom.py`):** Extract part lists and hand off to `bom` skill or distributor skills.
7. **Datasheet Verification:** Sync datasheets via `digikey` / `mouser` / `lcsc` and verify IC pin functions against `datasheets` skill facts.
8. **EMC Risk Audit:** Assess switching frequencies, return paths, and clock line routing.
9. **SPICE Verification:** Simulate analog filters, voltage dividers, or power subcircuits if `ngspice` / `ltspice` / `xyce` is installed.

## Reference Guides

- `references/eagle-xml-schema.md` — XML tag definitions and document structure.
- `references/erc-drc-rules.md` — Dictionary of all ERC/DRC rule codes and severities.
- `references/report-generation.md` — Report structure and presentation rules.
