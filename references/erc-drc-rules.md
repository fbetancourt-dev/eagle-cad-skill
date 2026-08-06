# EAGLE CAD ERC and DRC Rule Catalogue

Taxonomy of rule codes, severities, and check definitions for EAGLE CAD schematic and board analysis.

## Rule Code Dictionary

| Rule ID | Domain | Default Severity | Category | Description |
|---------|--------|------------------|----------|-------------|
| `SCH-ERC-001` | Schematic | `high` | Connection | Unconnected pin on IC / Active Component |
| `SCH-ERC-002` | Schematic | `medium` | Connectivity | Floating net with only 1 pinref connection |
| `SCH-ERC-003` | Schematic | `blocker` | Power | Power domain conflict / Short circuit (e.g. GND to VCC) |
| `SCH-ERC-004` | Schematic | `medium` | Decoupling | Missing decoupling capacitor on IC power supply pins |
| `SCH-ERC-005` | Schematic | `low` | Control | Missing pull-up / pull-down resistor on RESET or ENABLE lines |
| `SCH-ERC-006` | Schematic | `medium` | Clock | Quartz crystal without load capacitors to ground |
| `SCH-ERC-007` | Schematic | `low` | Naming | Auto-generated net name (`N$1`) on communication/interface signals |
| `PCB-DRC-001` | Board | `medium` | Trace | Trace width below minimum fabrication threshold (< 0.15 mm / 6 mil) |
| `PCB-DRC-002` | Board | `medium` | Via | Via drill diameter below minimum drill limit (< 0.30 mm / 12 mil) |
| `PCB-DRC-003` | Board | `high` | Routing | Unrouted signal / airwire between component pads |
| `PCB-DRC-004` | Board | `medium` | Silkscreen | Silkscreen text or graphics overlapping exposed copper pads |
| `PCB-DRC-005` | Board | `medium` | Annular | Annular ring width insufficient for via drill |
| `PCB-DRC-006` | Board | `low` | Placement | Component or copper element placed too close to board edge (< 0.5 mm) |
| `CROSS-001` | Cross | `high` | Mismatch | Schematic part missing on PCB layout placement |
| `CROSS-002` | Cross | `medium` | Mismatch | Component value mismatch between schematic and board |
| `CROSS-003` | Cross | `medium` | Mismatch | Schematic net missing from PCB board signals list |

## Severities Defined

- **`blocker`**: Must be resolved before fabrication. Causes immediate hardware dysfunction or destructive failure (e.g., direct power short).
- **`high`**: Likely functional defect, unrouted connection, or unplaced component.
- **`medium`**: Potential reliability issue, thin trace width, or missing decoupling capacitor.
- **`low`**: Minor aesthetic, net naming, or marginal placement warning.
- **`info`**: Informational note or design metric.
