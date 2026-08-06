# EAGLE Design Review Report Generation Guide

Format contract for producing engineering design review reports from EAGLE CAD analysis data.

## Required Report Sections

1. **Executive Summary & Verdict:** Overall recommendation (`PASSED`, `PASSED WITH WARNINGS`, `NEEDS REVISION`, `CRITICAL BLOCKERS`).
2. **Project Vitals:** Board dimensions, surface area, total parts, instances, nets, layers, and trace density.
3. **Blockers & High-Severity Issues:** Table listing all `blocker` and `high` findings with ID, Title, Description, and Evidence.
4. **Schematic ERC Analysis:** Detailed findings for schematic connectivity, decoupling, resets, and net naming.
5. **PCB Layout DRC & DFM Analysis:** Findings for track widths, via drill sizes, unrouted airwires, and board edge margins.
6. **Schematic vs PCB Cross-Verification:** Results of consistency cross-checking.
7. **Datasheet & Life-Cycle Handoff Notes:** Handoff notes for `datasheets`, `bom`, `emc`, and `spice` integration.
