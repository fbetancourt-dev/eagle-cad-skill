#!/usr/bin/env python3
"""
EAGLE CAD XML Parser Engine (.sch and .brd files)
Parses EAGLE CAD v6.0 - v9.x XML files into structured Python dicts/JSON.
"""

import xml.etree.ElementTree as ET
import json
import os
import sys

class EagleParser:
    def __init__(self, sch_path=None, brd_path=None):
        self.sch_path = sch_path
        self.brd_path = brd_path
        self.gates_map = {}
        self.data = {
            "name": "",
            "layers": {},
            "schematic": {
                "instances": [],
                "parts": {},
                "nets": [],
                "symbols": {},
                "plain": []
            },
            "board": {
                "elements": [],
                "signals": [],
                "packages": {},
                "dimension": [],
                "plain": [],
                "holes": []
            }
        }

    def parse(self):
        if self.brd_path and os.path.exists(self.brd_path):
            self.data["name"] = os.path.splitext(os.path.basename(self.brd_path))[0]
        elif self.sch_path and os.path.exists(self.sch_path):
            self.data["name"] = os.path.splitext(os.path.basename(self.sch_path))[0]

        if self.sch_path and os.path.exists(self.sch_path):
            self._parse_schematic()
        if self.brd_path and os.path.exists(self.brd_path):
            self._parse_board()
            
        return self.data

    def _parse_layers(self, root):
        layers_node = root.find(".//layers")
        if layers_node is not None:
            for layer in layers_node.findall("layer"):
                num = int(layer.get("number", 0))
                self.data["layers"][num] = {
                    "name": layer.get("name", ""),
                    "color": layer.get("color", "1"),
                    "visible": layer.get("visible", "yes") == "yes",
                    "active": layer.get("active", "yes") == "yes"
                }

    def _parse_schematic(self):
        try:
            tree = ET.parse(self.sch_path)
        except Exception as e:
            raise RuntimeError(f"Failed to parse EAGLE schematic XML '{self.sch_path}': {e}")
        
        root = tree.getroot()
        self._parse_layers(root)
        
        schematic_node = root.find(".//schematic")
        if schematic_node is None:
            return

        # 1. Parse symbol libraries & deviceset gate maps
        libraries = schematic_node.find("libraries")
        if libraries is not None:
            for library in libraries.findall("library"):
                lib_name = library.get("name")
                
                devicesets_node = library.find("devicesets")
                if devicesets_node is not None:
                    for deviceset in devicesets_node.findall("deviceset"):
                        ds_name = deviceset.get("name")
                        gates_node = deviceset.find("gates")
                        if gates_node is not None:
                            for gate in gates_node.findall("gate"):
                                gate_name = gate.get("name")
                                sym_name = gate.get("symbol")
                                gate_x = float(gate.get("x", 0))
                                gate_y = float(gate.get("y", 0))
                                if lib_name not in self.gates_map:
                                    self.gates_map[lib_name] = {}
                                if ds_name not in self.gates_map[lib_name]:
                                    self.gates_map[lib_name][ds_name] = {}
                                self.gates_map[lib_name][ds_name][gate_name] = {
                                    "symbol": sym_name,
                                    "x": gate_x,
                                    "y": gate_y
                                }

                symbols_node = library.find("symbols")
                if symbols_node is not None:
                    for symbol in symbols_node.findall("symbol"):
                        sym_name = symbol.get("name")
                        sym_key = f"{lib_name}_{sym_name}"
                        
                        sym_data = {
                            "name": sym_name,
                            "library": lib_name,
                            "wires": [],
                            "pins": [],
                            "texts": [],
                            "rectangles": [],
                            "circles": [],
                            "frames": []
                        }
                        
                        for f in symbol.findall("frame"):
                            sym_data["frames"].append({
                                "x1": float(f.get("x1", 0)),
                                "y1": float(f.get("y1", 0)),
                                "x2": float(f.get("x2", 0)),
                                "y2": float(f.get("y2", 0)),
                                "columns": int(f.get("columns", 0)),
                                "rows": int(f.get("rows", 0)),
                                "layer": int(f.get("layer", 94))
                            })
                        
                        for w in symbol.findall("wire"):
                            curve = w.get("curve")
                            sym_data["wires"].append({
                                "x1": float(w.get("x1", 0)),
                                "y1": float(w.get("y1", 0)),
                                "x2": float(w.get("x2", 0)),
                                "y2": float(w.get("y2", 0)),
                                "width": float(w.get("width", 0.15)),
                                "layer": int(w.get("layer", 94)),
                                "curve": float(curve) if curve is not None else None
                            })
                        for p in symbol.findall("pin"):
                            sym_data["pins"].append({
                                "name": p.get("name"),
                                "x": float(p.get("x", 0)),
                                "y": float(p.get("y", 0)),
                                "visible": p.get("visible", "both"),
                                "length": p.get("length", "middle"),
                                "direction": p.get("direction", "pas"),
                                "function": p.get("function", "none"),
                                "rot": p.get("rot", "R0")
                            })
                        for t in symbol.findall("text"):
                            sym_data["texts"].append({
                                "text": t.text or "",
                                "x": float(t.get("x", 0)),
                                "y": float(t.get("y", 0)),
                                "size": float(t.get("size", 1.5)),
                                "layer": int(t.get("layer", 94)),
                                "rot": t.get("rot", "R0")
                            })
                        for r in symbol.findall("rectangle"):
                            sym_data["rectangles"].append({
                                "x1": float(r.get("x1", 0)),
                                "y1": float(r.get("y1", 0)),
                                "x2": float(r.get("x2", 0)),
                                "y2": float(r.get("y2", 0)),
                                "layer": int(r.get("layer", 94))
                            })
                        for c in symbol.findall("circle"):
                            sym_data["circles"].append({
                                "x": float(c.get("x", 0)),
                                "y": float(c.get("y", 0)),
                                "radius": float(c.get("radius", 0)),
                                "width": float(c.get("width", 0)),
                                "layer": int(c.get("layer", 94))
                            })
                        
                        self.data["schematic"]["symbols"][sym_key] = sym_data

        # 2. Parse parts and sheet instances
        parts_node = schematic_node.find("parts")
        if parts_node is not None:
            for part in parts_node.findall("part"):
                p_name = part.get("name")
                self.data["schematic"]["parts"][p_name] = {
                    "name": p_name,
                    "library": part.get("library"),
                    "deviceset": part.get("deviceset"),
                    "device": part.get("device", ""),
                    "value": part.get("value", "")
                }

        sheets_node = schematic_node.find("sheets")
        if sheets_node is not None:
            for sheet in sheets_node.findall("sheet"):
                instances_node = sheet.find("instances")
                if instances_node is not None:
                    for inst in instances_node.findall("instance"):
                        part_name = inst.get("part")
                        part_info = self.data["schematic"]["parts"].get(part_name, {"library": "", "deviceset": "", "value": ""})
                        gate_name = inst.get("gate")
                        lib_name = part_info["library"]
                        ds_name = part_info["deviceset"]
                        
                        part_value = part_info["value"]
                        if not part_value:
                            part_value = ds_name
                        
                        sym_name = ds_name
                        gate_x = 0.0
                        gate_y = 0.0
                        if lib_name in self.gates_map and ds_name in self.gates_map[lib_name]:
                            gate_info = self.gates_map[lib_name][ds_name].get(gate_name, ds_name)
                            if isinstance(gate_info, dict):
                                sym_name = gate_info["symbol"]
                                gate_x = gate_info["x"]
                                gate_y = gate_info["y"]
                            else:
                                sym_name = gate_info
                        
                        smashed_attrs = {}
                        for attr in inst.findall("attribute"):
                            attr_name = attr.get("name", "").upper()
                            smashed_attrs[attr_name] = {
                                "x": float(attr.get("x", 0)),
                                "y": float(attr.get("y", 0)),
                                "size": float(attr.get("size", 1.778)),
                                "rot": attr.get("rot", "R0"),
                                "layer": int(attr.get("layer", 95))
                            }
                        
                        self.data["schematic"]["instances"].append({
                            "part": part_name,
                            "library": lib_name,
                            "deviceset": ds_name,
                            "symbol": sym_name,
                            "value": part_value,
                            "gate": gate_name,
                            "x": float(inst.get("x", 0)),
                            "y": float(inst.get("y", 0)),
                            "gate_x": gate_x,
                            "gate_y": gate_y,
                            "rot": inst.get("rot", "R0"),
                            "smashed": inst.get("smashed") == "yes",
                            "smashed_attrs": smashed_attrs
                        })

                # 3. Parse schematic nets
                nets_node = sheet.find("nets")
                if nets_node is not None:
                    for net in nets_node.findall("net"):
                        net_name = net.get("name")
                        net_data = {
                            "name": net_name,
                            "wires": [],
                            "junctions": [],
                            "pinrefs": [],
                            "labels": []
                        }
                        for segment in net.findall("segment"):
                            for w in segment.findall("wire"):
                                curve = w.get("curve")
                                net_data["wires"].append({
                                    "x1": float(w.get("x1", 0)),
                                    "y1": float(w.get("y1", 0)),
                                    "x2": float(w.get("x2", 0)),
                                    "y2": float(w.get("y2", 0)),
                                    "width": float(w.get("width", 0.15)),
                                    "layer": int(w.get("layer", 91)),
                                    "curve": float(curve) if curve is not None else None
                                })
                            for j in segment.findall("junction"):
                                net_data["junctions"].append({
                                    "x": float(j.get("x", 0)),
                                    "y": float(j.get("y", 0))
                                })
                            for pr in segment.findall("pinref"):
                                net_data["pinrefs"].append({
                                    "part": pr.get("part"),
                                    "gate": pr.get("gate"),
                                    "pin": pr.get("pin")
                                })
                            for lbl in segment.findall("label"):
                                net_data["labels"].append({
                                    "x": float(lbl.get("x", 0)),
                                    "y": float(lbl.get("y", 0)),
                                    "size": float(lbl.get("size", 1.778)),
                                    "layer": int(lbl.get("layer", 95)),
                                    "rot": lbl.get("rot", "R0"),
                                    "xref": lbl.get("xref", "no")
                                })
                        self.data["schematic"]["nets"].append(net_data)
                
                plain_node = sheet.find("plain")
                if plain_node is not None:
                    self._parse_plain_node(plain_node, self.data["schematic"]["plain"], is_board=False)

    def _parse_board(self):
        try:
            tree = ET.parse(self.brd_path)
        except Exception as e:
            raise RuntimeError(f"Failed to parse EAGLE board XML '{self.brd_path}': {e}")
        
        root = tree.getroot()
        self._parse_layers(root)
        
        board_node = root.find(".//board")
        if board_node is None:
            return

        # 1. Parse footprint libraries
        libraries = board_node.find("libraries")
        if libraries is not None:
            for library in libraries.findall("library"):
                lib_name = library.get("name")
                packages_node = library.find("packages")
                if packages_node is not None:
                    for pkg in packages_node.findall("package"):
                        pkg_name = pkg.get("name")
                        pkg_key = f"{lib_name}_{pkg_name}"
                        
                        pkg_data = {
                            "name": pkg_name,
                            "library": lib_name,
                            "wires": [],
                            "smds": [],
                            "pads": [],
                            "texts": [],
                            "holes": [],
                            "circles": [],
                            "polygons": []
                        }
                        
                        for w in pkg.findall("wire"):
                            curve = w.get("curve")
                            pkg_data["wires"].append({
                                "x1": float(w.get("x1", 0)),
                                "y1": float(w.get("y1", 0)),
                                "x2": float(w.get("x2", 0)),
                                "y2": float(w.get("y2", 0)),
                                "width": float(w.get("width", 0.127)),
                                "layer": int(w.get("layer", 21)),
                                "curve": float(curve) if curve is not None else None
                            })
                        for s in pkg.findall("smd"):
                            pkg_data["smds"].append({
                                "name": s.get("name"),
                                "x": float(s.get("x", 0)),
                                "y": float(s.get("y", 0)),
                                "dx": float(s.get("dx", 0)),
                                "dy": float(s.get("dy", 0)),
                                "layer": int(s.get("layer", 1)),
                                "rot": s.get("rot", "R0")
                            })
                        for p in pkg.findall("pad"):
                            pkg_data["pads"].append({
                                "name": p.get("name"),
                                "x": float(p.get("x", 0)),
                                "y": float(p.get("y", 0)),
                                "drill": float(p.get("drill", 0.6)),
                                "diameter": float(p.get("diameter", 0)),
                                "shape": p.get("shape", "round"),
                                "rot": p.get("rot", "R0")
                            })
                        for t in pkg.findall("text"):
                            pkg_data["texts"].append({
                                "text": t.text or "",
                                "x": float(t.get("x", 0)),
                                "y": float(t.get("y", 0)),
                                "size": float(t.get("size", 1.0)),
                                "layer": int(t.get("layer", 25)),
                                "rot": t.get("rot", "R0")
                            })
                        for h in pkg.findall("hole"):
                            pkg_data["holes"].append({
                                "x": float(h.get("x", 0)),
                                "y": float(h.get("y", 0)),
                                "drill": float(h.get("drill", 0))
                            })
                        for c in pkg.findall("circle"):
                            pkg_data["circles"].append({
                                "x": float(c.get("x", 0)),
                                "y": float(c.get("y", 0)),
                                "radius": float(c.get("radius", 0)),
                                "width": float(c.get("width", 0)),
                                "layer": int(c.get("layer", 21))
                            })
                        for poly in pkg.findall("polygon"):
                            poly_data = {
                                "width": float(poly.get("width", 0.127)),
                                "layer": int(poly.get("layer", 21)),
                                "vertices": []
                            }
                            for vertex in poly.findall("vertex"):
                                poly_data["vertices"].append({
                                    "x": float(vertex.get("x", 0)),
                                    "y": float(vertex.get("y", 0))
                                })
                            pkg_data["polygons"].append(poly_data)
                        
                        self.data["board"]["packages"][pkg_key] = pkg_data

        # 2. Parse board elements
        elements_node = board_node.find("elements")
        if elements_node is not None:
            for elem in elements_node.findall("element"):
                self.data["board"]["elements"].append({
                    "name": elem.get("name"),
                    "library": elem.get("library"),
                    "package": elem.get("package"),
                    "value": elem.get("value", ""),
                    "x": float(elem.get("x", 0)),
                    "y": float(elem.get("y", 0)),
                    "rot": elem.get("rot", "R0")
                })

        # 3. Parse signals, tracks, vias, contactrefs
        signals_node = board_node.find("signals")
        if signals_node is not None:
            for sig in signals_node.findall("signal"):
                sig_data = {
                    "name": sig.get("name"),
                    "wires": [],
                    "vias": [],
                    "contactrefs": [],
                    "polygons": []
                }
                for w in sig.findall("wire"):
                    curve = w.get("curve")
                    sig_data["wires"].append({
                        "x1": float(w.get("x1", 0)),
                        "y1": float(w.get("y1", 0)),
                        "x2": float(w.get("x2", 0)),
                        "y2": float(w.get("y2", 0)),
                        "width": float(w.get("width", 0.254)),
                        "layer": int(w.get("layer", 1)),
                        "curve": float(curve) if curve is not None else None
                    })
                for v in sig.findall("via"):
                    sig_data["vias"].append({
                        "x": float(v.get("x", 0)),
                        "y": float(v.get("y", 0)),
                        "drill": float(v.get("drill", 0.5)),
                        "diameter": float(v.get("diameter", 0.8)),
                        "shape": v.get("shape", "round")
                    })
                for cr in sig.findall("contactref"):
                    sig_data["contactrefs"].append({
                        "element": cr.get("element"),
                        "pad": cr.get("pad")
                    })
                for poly in sig.findall("polygon"):
                    poly_data = {
                        "width": float(poly.get("width", 0.254)),
                        "layer": int(poly.get("layer", 1)),
                        "vertices": []
                    }
                    for vertex in poly.findall("vertex"):
                        poly_data["vertices"].append({
                            "x": float(vertex.get("x", 0)),
                            "y": float(vertex.get("y", 0))
                        })
                    sig_data["polygons"].append(poly_data)
                self.data["board"]["signals"].append(sig_data)

        # 4. Parse board dimension (layer 20) and plain elements
        plain_node = board_node.find("plain")
        if plain_node is not None:
            self._parse_plain_node(plain_node, self.data["board"]["plain"], is_board=True)
 
        # 5. Parse mechanical holes
        holes_node = board_node.find("holes")
        if holes_node is not None:
            for h in holes_node.findall("hole"):
                self.data["board"]["holes"].append({
                    "x": float(h.get("x", 0)),
                    "y": float(h.get("y", 0)),
                    "drill": float(h.get("drill", 0.5))
                })

    def _parse_plain_node(self, plain_node, dest_list, is_board=False):
        for w in plain_node.findall("wire"):
            layer_num = int(w.get("layer", 1))
            curve = w.get("curve")
            wire_data = {
                "type": "wire",
                "x1": float(w.get("x1", 0)),
                "y1": float(w.get("y1", 0)),
                "x2": float(w.get("x2", 0)),
                "y2": float(w.get("y2", 0)),
                "width": float(w.get("width", 0.15)),
                "layer": layer_num,
                "curve": float(curve) if curve is not None else None
            }
            if is_board and layer_num == 20:
                self.data["board"]["dimension"].append(wire_data)
            else:
                dest_list.append(wire_data)
        for t in plain_node.findall("text"):
            dest_list.append({
                "type": "text",
                "text": t.text or "",
                "x": float(t.get("x", 0)),
                "y": float(t.get("y", 0)),
                "size": float(t.get("size", 1.0)),
                "layer": int(t.get("layer", 1)),
                "rot": t.get("rot", "R0")
            })
        for c in plain_node.findall("circle"):
            dest_list.append({
                "type": "circle",
                "x": float(c.get("x", 0)),
                "y": float(c.get("y", 0)),
                "radius": float(c.get("radius", 0)),
                "width": float(c.get("width", 0.15)),
                "layer": int(c.get("layer", 1))
            })
        for r in plain_node.findall("rectangle"):
            dest_list.append({
                "type": "rectangle",
                "x1": float(r.get("x1", 0)),
                "y1": float(r.get("y1", 0)),
                "x2": float(r.get("x2", 0)),
                "y2": float(r.get("y2", 0)),
                "layer": int(r.get("layer", 1))
            })
        for poly in plain_node.findall("polygon"):
            poly_data = {
                "type": "polygon",
                "width": float(poly.get("width", 0.15)),
                "layer": int(poly.get("layer", 1)),
                "vertices": []
            }
            for vertex in poly.findall("vertex"):
                poly_data["vertices"].append({
                    "x": float(vertex.get("x", 0)),
                    "y": float(vertex.get("y", 0))
                })
            dest_list.append(poly_data)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sch_file = sys.argv[1] if sys.argv[1].endswith(".sch") else None
        brd_file = sys.argv[1] if sys.argv[1].endswith(".brd") else (sys.argv[2] if len(sys.argv) > 2 else None)
        parser = EagleParser(sch_file, brd_file)
        res = parser.parse()
        print(json.dumps({
            "name": res["name"],
            "instances_count": len(res["schematic"]["instances"]),
            "nets_count": len(res["schematic"]["nets"]),
            "elements_count": len(res["board"]["elements"]),
            "signals_count": len(res["board"]["signals"])
        }, indent=2))
