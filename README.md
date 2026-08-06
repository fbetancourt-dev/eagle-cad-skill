# EAGLE CAD Agentic Skill (`eagle-cad-skill`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Antigravity Skill](https://img.shields.io/badge/Antigravity-Skill-purple.svg)](https://github.com/fbetancourt-dev/eagle-cad-skill)

An autonomous AI agent skill for **Autodesk & CadSoft EAGLE CAD** (`.sch` & `.brd`) schematic and PCB analysis, ERC/DRC auditing, schematic-vs-PCB cross-verification, BOM extraction, programmatic XML editing, and `.scr` command script generation.

Designed for seamless integration with **Google Antigravity**, **Claude Code**, and **Codex/MCP** environments.

---

## 🚀 Key Features

- 📑 **Native EAGLE XML Parser (`eagle_parser.py`):** High-speed parsing of `.sch` schematic and `.brd` board layout XML files (EAGLE v6.0 through EAGLE v9.6.2 and Fusion 360 Electronics).
- 🔍 **Schematic ERC Analyzer (`analyze_schematic.py`):** Automatically detects unconnected IC pins, floating single-connection nets, power domain conflicts, missing decoupling capacitors, reset/enable pullups, quartz crystal load caps, and auto-generated net names.
- 📐 **PCB Layout DRC / DFM Analyzer (`analyze_pcb.py`):** Calculates board dimensions and surface area, flags thin trace widths (< 0.15mm / 6mil), small via drill sizes (< 0.3mm / 12mil), unrouted airwire signals, and edge clearances.
- 🔄 **Schematic-vs-Board Cross Analysis (`cross_analysis.py`):** Cross-verifies schematic instance parts against board elements, checking for missing components, value mismatches, and unrouted net signals.
- 📊 **BOM Extractor (`export_bom.py`):** Aggregates component counts, values, packages, and designators into structured JSON and CSV formats for integration with distributor skills (`digikey`, `mouser`, `lcsc`, `element14`).
- ✍️ **Programmatic XML Editor (`edit_eagle.py`):** Allows programmatic modification of component values, net names, and part attributes with clean DTD-compliant XML re-serialization.
- 📜 **Command Script Generator (`generate_scr.py`):** Compiles executable EAGLE CAD batch script files (`.scr`) for GUI automation.

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

## 🛠️ Usage

### 1. Analyze EAGLE Schematic (ERC Check)

```bash
python3 ~/.gemini/config/skills/eagle/scripts/analyze_schematic.py my_design.sch
```

### 2. Analyze PCB Layout (DRC & DFM Check)

```bash
python3 ~/.gemini/config/skills/eagle/scripts/analyze_pcb.py my_design.brd
```

### 3. Schematic vs PCB Cross-Verification

```bash
python3 ~/.gemini/config/skills/eagle/scripts/cross_analysis.py my_design.sch my_design.brd
```

### 4. Extract Structured BOM

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
