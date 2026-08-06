#!/usr/bin/env python3
"""
===============================================================================
Unified Hybrid PCB Autorouter Engine for EAGLE CAD (.sch and .brd)
===============================================================================
Author: Francisco Betancourt (Antigravity Agentic Assistant)
Description:
    Provides a unified entry point supporting dual autorouting engines:
      1. 'astar'       -> Pure Python native 2D/3D A* grid pathfinding.
      2. 'freerouting' -> Specctra DSN/SES topological engine integration.
      3. 'auto'        -> Hybrid multi-tier mode: runs native A* grid search first,
                          falling back seamlessly to Freerouting if needed.
"""

import sys
import os
import json
import argparse
from autoroute_astar import AStarPCBRouter
from autoroute_freerouting import FreeroutingPipeline

def autoroute_board(brd_path, mode="auto", grid_step=0.5, freerouting_jar=None, output_path=None):
    """
    Executes autorouting on specified board path using selected mode.
    
    Args:
        brd_path (str): Path to input EAGLE .brd file.
        mode (str): Routing mode ('auto', 'astar', 'freerouting').
        grid_step (float): Resolution step in mm for A* grid search.
        freerouting_jar (str): Optional path to freerouting.jar.
        output_path (str): Optional output path for routed board file.
        
    Returns:
        dict: Execution status dictionary containing mode used and routing results.
    """
    print(f"==================================================")
    print(f"STARTING HYBRID PCB AUTOROUTER: {os.path.basename(brd_path)}")
    print(f"Mode: '{mode.upper()}' | Grid Step: {grid_step} mm")
    print(f"==================================================")

    target_out = output_path if output_path else brd_path

    # -------------------------------------------------------------------------
    # Mode 1 / Phase 1: Pure Python Native A* Grid Search
    # -------------------------------------------------------------------------
    if mode in ["astar", "auto"]:
        print("\n--- [Phase 1] Executing Pure Python Native A* Grid Search ---")
        router = AStarPCBRouter(brd_path, grid_step=grid_step)
        
        # Identify signals with 2+ contactrefs and 0 routed tracks
        unrouted_signals = []
        for sig in router.brd_data.get("signals", []):
            if len(sig.get("contactrefs", [])) >= 2 and len(sig.get("wires", [])) == 0:
                unrouted_signals.append(sig["name"])

        print(f"Unrouted airwires identified: {len(unrouted_signals)}")

        routed_count = 0
        failed_signals = []

        for sig_name in unrouted_signals:
            res = router.route_airwire_signal(sig_name)
            if res:
                print(f"  ✓ A* routed '{sig_name}' ({len(res['wires'])} tracks, {len(res['vias'])} vias)")
                routed_count += 1
            else:
                failed_signals.append(sig_name)
                print(f"  ✗ A* could not find path for '{sig_name}'")

        # If all signals routed successfully via A*, finish early
        if len(failed_signals) == 0 and len(unrouted_signals) > 0:
            print(f"\n🎉 ALL SIGNALS SUCCESSFULLY ROUTED VIA NATIVE A*!")
            return {"status": "SUCCESS", "mode_used": "astar", "routed_count": routed_count, "failed_count": 0}

        if mode == "astar" or len(failed_signals) == 0:
            return {"status": "PARTIAL" if failed_signals else "SUCCESS", "mode_used": "astar", "routed_count": routed_count, "failed_count": len(failed_signals)}

    # -------------------------------------------------------------------------
    # Mode 2 / Phase 2: Freerouting Topological Engine Fallback
    # -------------------------------------------------------------------------
    if mode in ["freerouting", "auto"]:
        print("\n--- [Phase 2] Commencing Freerouting Topological Engine ---")
        pipeline = FreeroutingPipeline(brd_path, freerouting_jar=freerouting_jar)
        dsn_path = brd_path.replace(".brd", ".dsn")
        pipeline.export_dsn(dsn_path)
        print(f"  Exported Specctra DSN file to '{dsn_path}'")
        
        jar_path = freerouting_jar or os.environ.get("FREEROUTING_JAR", "freerouting.jar")
        if os.path.exists(jar_path):
            ses_path = brd_path.replace(".brd", ".ses")
            try:
                pipeline.run_freerouting_headless(dsn_path, ses_path)
                print(f"  ✓ Freerouting completed. Session saved to '{ses_path}'")
                return {"status": "SUCCESS", "mode_used": "freerouting", "dsn_file": dsn_path, "ses_file": ses_path}
            except Exception as e:
                print(f"  ✗ Freerouting execution note: {e}")
        else:
            print(f"  ℹ Specctra DSN ready at '{dsn_path}'. (Optional freerouting.jar not specified).")
            return {"status": "DSN_READY", "mode_used": "freerouting", "dsn_file": dsn_path}

    return {"status": "COMPLETE", "mode_used": mode}

def main():
    parser = argparse.ArgumentParser(description="Unified Hybrid PCB Autorouter Engine for EAGLE CAD")
    parser.add_argument("brd_path", help="Path to .brd EAGLE board file")
    parser.add_argument("--mode", choices=["auto", "astar", "freerouting"], default="auto", help="Autorouting mode (default: auto)")
    parser.add_argument("--grid-step", type=float, default=0.5, help="Grid step size in mm for A* (default: 0.5)")
    parser.add_argument("--freerouting-jar", help="Path to freerouting.jar executable for Freerouting mode")
    parser.add_argument("-o", "--output", help="Output .brd file path")

    args = parser.parse_args()

    if not os.path.exists(args.brd_path):
        print(f"Error: File '{args.brd_path}' not found.", file=sys.stderr)
        sys.exit(1)

    res = autoroute_board(
        args.brd_path,
        mode=args.mode,
        grid_step=args.grid_step,
        freerouting_jar=args.freerouting_jar,
        output_path=args.output
    )
    print("\nResult:", json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
