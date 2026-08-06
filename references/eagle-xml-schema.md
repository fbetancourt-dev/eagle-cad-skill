# EAGLE CAD XML Format Reference

Autodesk / CadSoft EAGLE CAD v6.0+ uses an XML-based file format for schematics (`.sch`), board layouts (`.brd`), and component libraries (`.lbr`).

## Core Document Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE eagle SYSTEM "eagle.dtd">
<eagle version="9.6.2">
  <drawing>
    <settings>...</settings>
    <grid ... />
    <layers>
      <layer number="1" name="Top" color="4" fill="1" visible="yes" active="yes"/>
      <layer number="16" name="Bottom" color="1" fill="1" visible="yes" active="yes"/>
      ...
    </layers>
    <schematic> <!-- or <board> -->
      ...
    </schematic>
  </drawing>
</eagle>
```

## Schematic Elements (`<schematic>`)

- `<libraries>`: Contains `<library>` declarations, defining symbols (`<symbol>`), footprints (`<package>`), and component sets (`<deviceset>`).
- `<parts>`: List of component instances (`<part name="C1" library="adafruit" deviceset="C-US" device="0805" value="10uF"/>`).
- `<sheets>`: Contains `<sheet>` definitions.
  - `<instances>`: Placed symbol gates on the sheet (`<instance part="C1" gate="G$1" x="25.4" y="50.8" rot="R90"/>`).
  - `<nets>`: Electrical connections (`<net name="VCC" class="0">`).
    - `<segment>`: Group of wires, junctions, pinrefs, and net labels on a sheet segment.
      - `<wire x1="..." y1="..." x2="..." y2="..." width="0.15" layer="91"/>`
      - `<junction x="..." y="..."/>`
      - `<pinref part="C1" gate="G$1" pin="1"/>`
      - `<label x="..." y="..." size="1.778" layer="95" rot="R0" xref="yes"/>`

## Board Elements (`<board>`)

- `<libraries>`: Embedded footprints (`<package>`) used by board elements.
- `<elements>`: Placed physical components (`<element name="C1" library="adafruit" package="0805" value="10uF" x="12.7" y="15.2" rot="R180"/>`).
- `<signals>`: Routed electrical nets (`<signal name="VCC">`).
  - `<contactref element="C1" pad="1"/>`: Pad connections.
  - `<wire x1="..." y1="..." x2="..." y2="..." width="0.4064" layer="1"/>`: Routed copper tracks.
  - `<via x="..." y="..." drill="0.5" diameter="0.8" shape="round"/>`: Inter-layer vias.
  - `<polygon width="0.254" layer="1">`: Copper pour areas.
- `<plain>`: Board outline (`<wire layer="20">`), mechanical cutouts, and silkscreen text.
- `<holes>`: Non-plated mechanical mounting holes (`<hole x="..." y="..." drill="3.2"/>`).

## Layer Standards

- **Layer 1:** Top (Copper)
- **Layer 16:** Bottom (Copper)
- **Layer 20:** Dimension (Board Outline)
- **Layer 21:** tPlace (Top Silkscreen Outline)
- **Layer 22:** bPlace (Bottom Silkscreen Outline)
- **Layer 25:** tNames (Top Designator Text)
- **Layer 26:** bNames (Bottom Designator Text)
- **Layer 91:** Nets (Schematic Wires)
- **Layer 94:** Symbols (Schematic Symbol Wires)
- **Layer 95:** Names (Schematic Designator Text)
- **Layer 96:** Values (Schematic Value Text)
