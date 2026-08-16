#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agt_demo.config import load_config
from agt_demo.governance import audit_path, events_path
from agt_demo.agents import run_orchestrator

def main():
    cfg = load_config()
    for p in (audit_path(cfg), events_path(cfg)):
        if p.exists():
            p.unlink()
    print("=" * 72)
    print("  Agent Control Lab · knowledge → critic → compliance")
    print("=" * 72)
    final = run_orchestrator(cfg)
    print("DONE")
    print(f"  TTL     : {final.get('ttl_path')}")
    print(f"  Verdict : {str(final.get('compliance_verdict') or '')[:120]}")

if __name__ == "__main__":
    main()
