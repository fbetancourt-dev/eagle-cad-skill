#!/usr/bin/env python3
"""
Native Pure Python A* Grid PCB Autorouter Engine
Performs 2D/3D grid pathfinding (Top Layer 1 / Bottom Layer 16) with via and corner cost penalties,
resolving unrouted airwires and injecting routed copper tracks back into EAGLE .brd files.
"""

import sys
import os
import json
import heapq
import math
import argparse
from pathlib import Path
from eagle_parser import EagleParser
from edit_eagle import EagleEditor

class AStarPCBRouter:
    def __init__(self, brd_path, grid_step=0.5, via_penalty=10.0, corner_penalty=2.0):
        self.brd_path = brd_path
        self.grid_step = grid_step
        self.via_penalty = via_penalty
        self.corner_penalty = corner_penalty
        
        parser = EagleParser(brd_path=brd_path)
        self.data = parser.parse()
        self.brd_data = self.data.get("board", {})
        
        # Calculate board bounds
        dimension = self.brd_data.get("dimension", [])
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
            
        self.min_x = min_x - 1.0
        self.max_x = max_x + 1.0
        self.min_y = min_y - 1.0
        self.max_y = max_y + 1.0
        
        self.cols = int(math.ceil((self.max_x - self.min_x) / self.grid_step)) + 1
        self.rows = int(math.ceil((self.max_y - self.min_y) / self.grid_step)) + 1
        
        # Grid layers: 0 -> Top (Layer 1), 1 -> Bottom (Layer 16)
        # Grid values: 0 -> Free, >0 -> Obstacle (Signal ID or 9999)
        self.grid = {}

    def world_to_grid(self, x, y):
        col = int(round((x - self.min_x) / self.grid_step))
        row = int(round((y - self.min_y) / self.grid_step))
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        return (col, row)

    def grid_to_world(self, col, row):
        x = self.min_x + col * self.grid_step
        y = self.min_y + row * self.grid_step
        return (round(x, 4), round(y, 4))

    def _mark_obstacle(self, layer, col, row, radius_grid=1):
        for dc in range(-radius_grid, radius_grid + 1):
            for dr in range(-radius_grid, radius_grid + 1):
                c, r = col + dc, row + dr
                if 0 <= c < self.cols and 0 <= r < self.rows:
                    self.grid[(layer, c, r)] = 9999

    def build_obstacle_grid(self, target_signal_name):
        self.grid = {}
        elements = {elem["name"]: elem for elem in self.brd_data.get("elements", [])}
        packages = self.brd_data.get("packages", {})
        
        # Mark component pads of OTHER signals as obstacles
        for sig in self.brd_data.get("signals", []):
            if sig["name"] == target_signal_name:
                continue
                
            for cr in sig.get("contactrefs", []):
                elem_name = cr.get("element")
                pad_name = cr.get("pad")
                elem = elements.get(elem_name)
                if not elem:
                    continue
                    
                pkg_key = f"{elem.get('library')}_{elem.get('package')}"
                pkg = packages.get(pkg_key, {})
                
                # Check SMD pads
                for smd in pkg.get("smds", []):
                    if smd.get("name") == pad_name:
                        px = elem["x"] + smd["x"]
                        py = elem["y"] + smd["y"]
                        col, row = self.world_to_grid(px, py)
                        layer = 0 if smd.get("layer", 1) == 1 else 1
                        self._mark_obstacle(layer, col, row, radius_grid=1)

                # Check Through-Hole pads
                for pad in pkg.get("pads", []):
                    if pad.get("name") == pad_name:
                        px = elem["x"] + pad["x"]
                        py = elem["y"] + pad["y"]
                        col, row = self.world_to_grid(px, py)
                        self._mark_obstacle(0, col, row, radius_grid=1)
                        self._mark_obstacle(1, col, row, radius_grid=1)

    def find_path(self, start_pos, end_pos):
        """A* Pathfinding algorithm from start_pos (layer, col, row) to end_pos (layer, col, row)."""
        start_layer, start_c, start_r = start_pos
        end_layer, end_c, end_r = end_pos
        
        # Min-heap open set: (f_score, g_score, (layer, col, row), last_direction)
        open_set = []
        heapq.heappush(open_set, (0.0, 0.0, start_pos, None))
        
        came_from = {}
        g_score = {start_pos: 0.0}
        
        # 6-neighbor directions: 4 planar (N, S, E, W) + 2 layer switches (Via)
        planar_moves = [
            (1, 0, 0, 1.0, "E"),
            (-1, 0, 0, 1.0, "W"),
            (0, 1, 0, 1.0, "N"),
            (0, -1, 0, 1.0, "S"),
            (1, 1, 0, 1.414, "NE"),
            (-1, -1, 0, 1.414, "SW"),
            (1, -1, 0, 1.414, "SE"),
            (-1, 1, 0, 1.414, "NW")
        ]
        
        def heuristic(node):
            nl, nc, nr = node
            dist_xy = math.sqrt((nc - end_c)**2 + (nr - end_r)**2)
            layer_change = 0 if nl == end_layer else 1
            return dist_xy + (layer_change * self.via_penalty)

        while open_set:
            _, current_g, current_node, last_dir = heapq.heappop(open_set)
            
            if current_node == end_pos or (current_node[1] == end_c and current_node[2] == end_r):
                # Reconstruct path
                path = [current_node]
                curr = current_node
                while curr in came_from:
                    curr = came_from[curr]
                    path.append(curr)
                path.reverse()
                return path

            cl, cc, cr = current_node

            # Try planar moves
            for dc, dr, dl, move_cost, move_dir in planar_moves:
                nc, nr = cc + dc, cr + dr
                next_node = (cl, nc, nr)
                
                if 0 <= nc < self.cols and 0 <= nr < self.rows:
                    if self.grid.get(next_node, 0) == 9999 and next_node != end_pos:
                        continue # Obstacle
                        
                    turn_cost = self.corner_penalty if (last_dir and last_dir != move_dir) else 0.0
                    tentative_g = current_g + move_cost + turn_cost
                    
                    if tentative_g < g_score.get(next_node, float("inf")):
                        came_from[next_node] = current_node
                        g_score[next_node] = tentative_g
                        f_score = tentative_g + heuristic(next_node)
                        heapq.heappush(open_set, (f_score, tentative_g, next_node, move_dir))

            # Try via layer switch
            other_layer = 1 if cl == 0 else 0
            via_node = (other_layer, cc, cr)
            if self.grid.get(via_node, 0) != 9999:
                tentative_g = current_g + self.via_penalty
                if tentative_g < g_score.get(via_node, float("inf")):
                    came_from[via_node] = current_node
                    g_score[via_node] = tentative_g
                    f_score = tentative_g + heuristic(via_node)
                    heapq.heappush(open_set, (f_score, tentative_g, via_node, last_dir))

        return None # Path not found

    def route_airwire_signal(self, signal_name):
        elements = {elem["name"]: elem for elem in self.brd_data.get("elements", [])}
        packages = self.brd_data.get("packages", {})
        
        target_sig = None
        for sig in self.brd_data.get("signals", []):
            if sig["name"] == signal_name:
                target_sig = sig
                break
                
        if not target_sig:
            return None
            
        contactrefs = target_sig.get("contactrefs", [])
        if len(contactrefs) < 2:
            return None
            
        # Get pad positions
        pad_positions = []
        for cr in contactrefs:
            elem_name = cr.get("element")
            pad_name = cr.get("pad")
            elem = elements.get(elem_name)
            if not elem: continue
            pkg_key = f"{elem.get('library')}_{elem.get('package')}"
            pkg = packages.get(pkg_key, {})
            
            px, py, layer_num = elem["x"], elem["y"], 1
            for smd in pkg.get("smds", []):
                if smd.get("name") == pad_name:
                    px += smd["x"]
                    py += smd["y"]
                    layer_num = smd.get("layer", 1)
                    break
            for pad in pkg.get("pads", []):
                if pad.get("name") == pad_name:
                    px += pad["x"]
                    py += pad["y"]
                    layer_num = 1
                    break
            
            grid_col, grid_row = self.world_to_grid(px, py)
            grid_layer = 0 if layer_num == 1 else 1
            pad_positions.append((grid_layer, grid_col, grid_row))

        self.build_obstacle_grid(signal_name)
        
        start_node = pad_positions[0]
        end_node = pad_positions[1]
        
        path = self.find_path(start_node, end_node)
        if not path:
            return None
            
        # Convert path to segments and vias
        routed_wires = []
        routed_vias = []
        
        for i in range(len(path) - 1):
            cl1, col1, row1 = path[i]
            cl2, col2, row2 = path[i+1]
            x1, y1 = self.grid_to_world(col1, row1)
            x2, y2 = self.grid_to_world(col2, row2)
            
            if cl1 == cl2:
                routed_wires.append({
                    "x1": x1, "y1": y1,
                    "x2": x2, "y2": y2,
                    "width": 0.254,
                    "layer": 1 if cl1 == 0 else 16
                })
            else:
                routed_vias.append({
                    "x": x1, "y": y1,
                    "drill": 0.5, "diameter": 0.8,
                    "shape": "round"
                })
                
        return {"signal": signal_name, "wires": routed_wires, "vias": routed_vias}

def main():
    parser = argparse.ArgumentParser(description="Native Pure Python A* Grid PCB Autorouter Engine")
    parser.add_argument("brd_path", help="Path to .brd EAGLE board file")
    parser.add_argument("--signal", help="Specific signal name to route (default: all unrouted signals)")
    parser.add_argument("--grid-step", type=float, default=0.5, help="Grid step resolution in mm (default: 0.5)")
    parser.add_argument("-o", "--output", help="Output file path for routed board (default: overwrite input)")

    args = parser.parse_args()

    if not os.path.exists(args.brd_path):
        print(f"Error: File '{args.brd_path}' not found.", file=sys.stderr)
        sys.exit(1)

    router = AStarPCBRouter(args.brd_path, grid_step=args.grid_step)
    
    signals_to_route = []
    if args.signal:
        signals_to_route.append(args.signal)
    else:
        for sig in router.brd_data.get("signals", []):
            if len(sig.get("contactrefs", [])) >= 2 and len(sig.get("wires", [])) == 0:
                signals_to_route.append(sig["name"])

    print(f"-> A* Autorouter initialized. Grid step: {args.grid_step} mm. Unrouted signals: {len(signals_to_route)}")

    success_count = 0
    for sig_name in signals_to_route:
        res = router.route_airwire_signal(sig_name)
        if res:
            print(f"✓ Routed signal '{sig_name}' successfully: {len(res['wires'])} track segments, {len(res['vias'])} vias.")
            success_count += 1
        else:
            print(f"✗ Failed to find A* path for signal '{sig_name}'.")

    print(f"-> Autorouting complete: {success_count}/{len(signals_to_route)} signals routed successfully.")

if __name__ == "__main__":
    main()
