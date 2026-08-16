#!/usr/bin/env python3
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agt_demo.config import load_config
from agt_demo.governance import audit_path, events_path
from agt_demo.agt_layers import SreMonitor, sre_state_path
from agt_demo.agents.orchestrator import CircuitOpenError, run_orchestrator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sre-demo", action="store_true")
    parser.add_argument("--sre-reset", action="store_true")
    args = parser.parse_args()
    cfg = load_config()
    if args.sre_reset:
        SreMonitor.load(sre_state_path(cfg)).reset()
        print(f"SRE reset: {sre_state_path(cfg)}")
        return
    for p in (audit_path(cfg), events_path(cfg)):
        if p.exists():
            p.unlink()
    print("=" * 72)
    print("  Agent Control Lab · knowledge → critic → compliance")
    print("=" * 72)
    try:
        final = run_orchestrator(cfg, sre_demo=args.sre_demo)
    except CircuitOpenError as e:
        print(f"BLOCKED: {e}")
        sys.exit(2)
    print("DONE")
    print(f"  TTL     : {final.get('ttl_path')}")
    print(f"  Verdict : {str(final.get('compliance_verdict') or '')[:120]}")
    print(f"  SRE     : {sre_state_path(cfg)}")


if __name__ == "__main__":
    main()
