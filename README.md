# EAGLE CAD Agentic Skill (`eagle-cad-skill`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Antigravity Skill](https://img.shields.io/badge/Antigravity-Skill-purple.svg)](https://github.com/fbetancourt-dev/eagle-cad-skill)

An autonomous AI agent skill for **Autodesk & CadSoft EAGLE CAD** (`.sch` & `.brd`) schematic and PCB analysis, ERC/DRC auditing, schematic-vs-PCB cross-verification, BOM extraction, programmatic XML editing, and `.scr` command script generation.

Designed for seamless integration with **Google Antigravity**, **Claude Code**, and **Codex/MCP** environments.

---

## 📊 Comprehensive Skill Capabilities Matrix

| Feature / Domain | Module / Script | Coverage & Detail Level | Execution Mode |
| :--- | :--- | :--- | :---: |
| **Schematic XML Parsing** | `eagle_parser.py` | Full parsing of parts, symbol libraries, gate-to-symbol resolution, sheet instances, smashed text attributes, rotative offsets, and net pinrefs. | ⚡ Headless Pure Python |
| **PCB Layout XML Parsing** | `eagle_parser.py` | Full parsing of elements, footprint packages, SMD pads, TH pads, routed track wires, inter-layer vias, copper pour polygons, and mechanical holes. | ⚡ Headless Pure Python |
| **Board Geometry & Outline** | `analyze_pcb.py` | Automatic boundary detection on Layer 20 (Dimension), board width/height calculation ($\text{mm}$), and surface area estimation ($\text{cm}^2$). | ⚡ Headless Pure Python |
| **Electrical Rules Check (ERC)** | `analyze_schematic.py` | Automated 7-rule audit suite covering unconnected IC pins, floating single-node nets, power shorts, missing decoupling caps, reset pullups, and auto-generated net names. | ⚡ Headless Pure Python |
| **Design Rules Check (DRC/DFM)** | `analyze_pcb.py` | Automated 6-rule audit suite covering track width thresholds, via drill limits, unrouted airwires, silkscreen-over-pad overlaps, and board edge margins. | ⚡ Headless Pure Python |
| **Schematic-vs-PCB Verification** | `cross_analysis.py` | Consistency verification between schematic parts list and PCB elements, reporting unplaced components, value mismatches, and unmapped signals. | ⚡ Headless Pure Python |
| **BOM Extraction & Sourcing** | `export_bom.py` | Grouped component extraction (DeviceSet, Value, Package, Library, Quantity, Designators) exported as structured JSON or CSV for distributor integration. | ⚡ Headless Pure Python |
| **Programmatic XML Editing** | `edit_eagle.py` | Live DOM modifications: updating component values, renaming nets/signals, setting part MPN attributes, with DTD-compliant XML re-serialization. | ⚡ Headless Pure Python |
| **GUI Automation Scripting** | `generate_scr.py` | Programmatic compilation of executable EAGLE batch command scripts (`.scr`) for GUI automation (Grids, Adds, Values, Wires, Vias, Texts). | ⚡ Headless Pure Python |

---

## 🔬 Detailed Architecture & Module Breakdown

### 1. Native EAGLE XML Parser Engine (`scripts/eagle_parser.py`)
- **XML Format Compatibility:** Supports EAGLE XML v6.0 through v9.6.2 and Autodesk Fusion 360 Electronics.
- **Schematic Resolution:** Maps `<deviceset>` gates (`<gate>`) to symbol representations (`<symbol>`), resolving pin lengths, directions (Input, Output, Passive, Power), and functions (Dot, Clk).
- **PCB Geometry Extraction:** Resolves SMD pads (`<smd>`), Through-Hole pads (`<pad>`), copper pour polygons (`<polygon>`), vias (`<via>`), and silkscreen layers (21 tPlace, 22 bPlace, 25 tNames, 26 bNames).

### 2. Electrical Rules Check Engine (`scripts/analyze_schematic.py`)
Executes an automated rule audit suite on schematic netlists:
- **`SCH-ERC-001` (Unconnected Pin):** Identifies active IC pins with no electrical net connection.
- **`SCH-ERC-002` (Floating Net):** Flags single-pinref nets with dangling connections.
- **`SCH-ERC-003` (Power Pin Conflict):** Detects direct short circuits between distinct power domains.
- **`SCH-ERC-004` (Missing Decoupling Caps):** Audits power supply pins on active ICs for proper local decoupling capacitors.
- **`SCH-ERC-005` (Reset/Enable Control):** Checks for pull-up/pull-down resistors on reset (NRST) and enable (EN) lines.
- **`SCH-ERC-006` (Crystal Load Capacitors):** Verifies quartz crystals have grounding load capacitors.
- **`SCH-ERC-007` (Default Net Naming):** Identifies auto-generated net names (`N$1`) on critical communication lines.

### 3. Design Rules & Manufacturing Engine (`scripts/analyze_pcb.py`)
Audits physical board layouts against standard manufacturing limits:
- **`PCB-DRC-001` (Trace Width):** Flags copper tracks narrower than standard manufacturing thresholds ($< 0.15\text{ mm} / 6\text{ mil}$).
- **`PCB-DRC-002` (Via Drill Size):** Flags via drill holes below standard drill capabilities ($< 0.30\text{ mm} / 12\text{ mil}$).
- **`PCB-DRC-003` (Unrouted Airwires):** Detects multi-pad signals with zero routed copper tracks or polygons.
- **`PCB-DRC-004` (Silkscreen Over Pad):** Identifies silkscreen text overlapping exposed solder pads.
- **`PCB-DRC-005` (Annular Ring Width):** Checks minimum annular ring widths for via drill holes.
- **`PCB-DRC-006` (Board Edge Clearance):** Flags components or copper elements placed within $0.5\text{ mm}$ of the board edge.

### 4. Schematic-vs-PCB Cross-Analysis Engine (`scripts/cross_analysis.py`)
Ensures full synchronization between schematic capture and board layout:
- **`CROSS-001` (Missing Component):** Detects schematic components missing from the PCB layout.
- **`CROSS-002` (Value Mismatch):** Flags discrepancies between schematic part values and board element values.
- **`CROSS-003` (Unmapped Signal):** Identifies schematic nets missing from the board signal list.

### 5. Bill of Materials Extractor (`scripts/export_bom.py`)
- Groups identical component configurations by DeviceSet, Value, Package, and Library.
- Outputs clean, structured JSON or CSV ready for distributor integration (`digikey`, `mouser`, `lcsc`, `element14`).

### 6. Programmatic XML Editor (`scripts/edit_eagle.py`)
- Provides CLI and API methods to update part values, rename nets/signals, and add part attributes.
- Re-serializes DTD-compliant, pretty-formatted XML files ready for EAGLE CAD or Fusion 360.

### 7. GUI Script Generator (`scripts/generate_scr.py`)
- Compiles executable EAGLE CAD batch command files (`.scr`) for GUI automation.

---

## 📥 Installation

### Linux / macOS (One-Line Installer)

```bash
curl -sSL https://raw.githubusercontent.com/fbetancourt-dev/eagle-cad-skill/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
iwr -useb https://raw.githubusercontent.com/fbetancourt-dev/eagle-cad-skill/main/install.ps1 | iex
```

### Manual Installation

Clone or copy this repository into your Antigravity skills root:

```bash
mkdir -p ~/.gemini/config/skills/
git clone https://github.com/fbetancourt-dev/eagle-cad-skill.git ~/.gemini/config/skills/eagle
```

---

## 🛠️ Usage Examples

### 1. Run ERC Schematic Analysis

```bash
python3 ~/.gemini/config/skills/eagle/scripts/analyze_schematic.py my_design.sch
```

### 2. Run DRC & DFM PCB Layout Analysis

```bash
python3 ~/.gemini/config/skills/eagle/scripts/analyze_pcb.py my_design.brd
```

### 3. Run Schematic vs PCB Cross-Verification

```bash
python3 ~/.gemini/config/skills/eagle/scripts/cross_analysis.py my_design.sch my_design.brd
```

### 4. Export Structured BOM (CSV)

```bash
python3 ~/.gemini/config/skills/eagle/scripts/export_bom.py --sch my_design.sch --brd my_design.brd --format csv
```

### 5. Programmatically Edit EAGLE XML Files

```bash
python3 ~/.gemini/config/skills/eagle/scripts/edit_eagle.py my_design.sch --set-value R1 10k --rename-net GND AGND -o my_design_updated.sch
```

---

## 📚 Documentation & References

- [`references/eagle-xml-schema.md`](references/eagle-xml-schema.md) — EAGLE CAD XML document tag specification.
- [`references/erc-drc-rules.md`](references/erc-drc-rules.md) — Catalogue of all ERC/DRC rule codes and severity levels.
- [`references/report-generation.md`](references/report-generation.md) — Design review report template contract.

---

## 📜 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
