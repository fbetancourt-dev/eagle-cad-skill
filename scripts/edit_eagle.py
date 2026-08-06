#!/usr/bin/env python3
"""
EAGLE CAD XML Editor & Serializer Engine (.sch and .brd files)
Allows programmatic modification of component values, attributes, net names, and footprints,
re-serializing valid XML files for EAGLE CAD & Fusion 360 Electronics.
"""

import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import sys
import os
import argparse

class EagleEditor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()

    def set_part_value(self, part_name, new_value):
        """Update value of a component in .sch or .brd file."""
        found = False
        # Search schematic parts
        parts_node = self.root.find(".//parts")
        if parts_node is not None:
            for p in parts_node.findall("part"):
                if p.get("name") == part_name:
                    p.set("value", str(new_value))
                    found = True
                    
        # Search board elements
        elements_node = self.root.find(".//elements")
        if elements_node is not None:
            for e in elements_node.findall("element"):
                if e.get("name") == part_name:
                    e.set("value", str(new_value))
                    found = True
                    
        return found

    def rename_net(self, old_name, new_name):
        """Rename a net in schematic or signal in board."""
        count = 0
        # Schematic nets
        for net in self.root.findall(".//net"):
            if net.get("name") == old_name:
                net.set("name", new_name)
                count += 1
        # Board signals
        for sig in self.root.findall(".//signal"):
            if sig.get("name") == old_name:
                sig.set("name", new_name)
                count += 1
        return count

    def set_part_attribute(self, part_name, attr_name, attr_value):
        """Add or update an attribute on a component part."""
        parts_node = self.root.find(".//parts")
        if parts_node is None:
            return False
            
        for p in parts_node.findall("part"):
            if p.get("name") == part_name:
                # Look for existing attribute
                attr_elem = None
                for a in p.findall("attribute"):
                    if a.get("name") == attr_name:
                        attr_elem = a
                        break
                if attr_elem is None:
                    attr_elem = ET.SubElement(p, "attribute")
                    attr_elem.set("name", attr_name)
                attr_elem.set("value", str(attr_value))
                return True
        return False

    def save(self, output_path=None):
        """Save formatted EAGLE XML file."""
        target_path = output_path if output_path else self.file_path
        
        # Prettify XML structure while maintaining EAGLE header
        rough_string = ET.tostring(self.root, encoding="utf-8")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ")
        
        # Strip blank line artifacts introduced by minidom
        lines = [line for line in pretty_xml.split("\n") if line.strip()]
        
        # Write back to disk
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return target_path

def main():
    parser = argparse.ArgumentParser(description="EAGLE CAD XML Editor & Serializer Engine")
    parser.add_argument("file_path", help="Path to .sch or .brd EAGLE file")
    parser.add_argument("--set-value", nargs=2, metavar=("PART", "VALUE"), help="Set value for component (e.g. --set-value R1 10k)")
    parser.add_argument("--rename-net", nargs=2, metavar=("OLD_NET", "NEW_NET"), help="Rename net or signal")
    parser.add_argument("--set-attr", nargs=3, metavar=("PART", "ATTR_NAME", "ATTR_VAL"), help="Set part attribute (e.g. --set-attr R1 MPN PT0603)")
    parser.add_argument("-o", "--output", help="Output file path (default: overwrite input file)")

    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"Error: File '{args.file_path}' not found.", file=sys.stderr)
        sys.exit(1)

    editor = EagleEditor(args.file_path)
    modified = False

    if args.set_value:
        part, val = args.set_value
        if editor.set_part_value(part, val):
            print(f"Updated component '{part}' value to '{val}'.")
            modified = True
        else:
            print(f"Warning: Component '{part}' not found.", file=sys.stderr)

    if args.rename_net:
        old_net, new_net = args.rename_net
        count = editor.rename_net(old_net, new_net)
        if count > 0:
            print(f"Renamed net '{old_net}' -> '{new_net}' ({count} occurrence(s)).")
            modified = True
        else:
            print(f"Warning: Net '{old_net}' not found.", file=sys.stderr)

    if args.set_attr:
        part, attr_name, attr_val = args.set_attr
        if editor.set_part_attribute(part, attr_name, attr_val):
            print(f"Set attribute '{attr_name}={attr_val}' on part '{part}'.")
            modified = True
        else:
            print(f"Warning: Part '{part}' not found.", file=sys.stderr)

    if modified:
        saved_path = editor.save(args.output)
        print(f"Saved modified EAGLE file to: '{saved_path}'")
    else:
        print("No changes were requested or applied.")

if __name__ == "__main__":
    main()
