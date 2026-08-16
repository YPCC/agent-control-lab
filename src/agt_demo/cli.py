"""Console entry: agent-control-lab / acl"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Agent Control Lab")
    parser.add_argument(
        "--sre-demo",
        action="store_true",
        help="Record this run as a failure to exercise the persistent SRE circuit breaker",
    )
    parser.add_argument(
        "--sre-reset",
        action="store_true",
        help="Reset persistent SRE state (close circuit) and exit",
    )
    args = parser.parse_args(argv)

    from agt_demo.config import load_config, repo_root
    from agt_demo.governance import audit_path, events_path
    from agt_demo.agt_layers import SreMonitor, sre_state_path
    from agt_demo.agents.orchestrator import CircuitOpenError, run_orchestrator

    cfg = load_config()

    if args.sre_reset:
        mon = SreMonitor.load(sre_state_path(cfg))
        mon.reset()
        print(f"SRE state cleared: {sre_state_path(cfg)}")
        return

    for p in (audit_path(cfg), events_path(cfg)):
        if p.exists():
            p.unlink()

    print("=" * 72)
    print("  Agent Control Lab · Spec-driven LangGraph · AGT concept map")
    print("=" * 72)
    print(f"  Config : {repo_root() / 'config' / 'config.yaml'}")
    print()

    try:
        final = run_orchestrator(cfg, sre_demo=args.sre_demo)
    except CircuitOpenError as e:
        print(f"\nBLOCKED: {e}")
        print("  Reset: agent-control-lab --sre-reset")
        sys.exit(2)

    print()
    print("DONE")
    print(f"  TTL     : {final.get('ttl_path')}")
    print(f"  Verdict : {str(final.get('compliance_verdict') or '')[:120]}")
    print(f"  Audit   : {audit_path(cfg)}")
    print(f"  Events  : {events_path(cfg)}")
    print(f"  SRE     : {sre_state_path(cfg)}")
    print("  Dashboard: streamlit run dashboards/companion_app.py --server.port 8502")


if __name__ == "__main__":
    main()
