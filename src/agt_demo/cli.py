"""Console entry: agent-control-lab / acl"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Agent Control Lab — spec-driven LangGraph + AGT concept map"
    )
    parser.add_argument(
        "--sre-demo",
        action="store_true",
        help="Record this run as a failure (SRE circuit demo)",
    )
    parser.add_argument(
        "--sre-reset",
        action="store_true",
        help="Reset persistent SRE state and exit",
    )
    parser.add_argument(
        "--kill-switch",
        action="store_true",
        help="Engage Runtime kill switch for this process (all tools blocked)",
    )
    parser.add_argument(
        "--marketplace-init",
        action="store_true",
        help="Generate Ed25519 keypair + signed tool catalog, then exit",
    )
    parser.add_argument(
        "--marketplace-sign",
        action="store_true",
        help="Re-sign tool catalog with existing private key, then exit",
    )
    parser.add_argument(
        "--marketplace-tamper",
        action="store_true",
        help="Tamper one catalog signature for verify-fail demo, then exit",
    )
    parser.add_argument(
        "--marketplace-enforce",
        action="store_true",
        help="Override config: marketplace.enforce=true for this run",
    )
    args = parser.parse_args(argv)

    from agt_demo.config import load_config, repo_root
    from agt_demo.governance import audit_path, events_path
    from agt_demo.agt_layers import SreMonitor, sre_state_path, get_runtime_guard
    from agt_demo.agents.orchestrator import (
        CircuitOpenError,
        MarketplaceRejectedError,
        run_orchestrator,
    )

    cfg = load_config()

    if args.sre_reset:
        mon = SreMonitor.load(sre_state_path(cfg))
        mon.reset()
        print(f"SRE state cleared: {sre_state_path(cfg)}")
        return

    if args.marketplace_init:
        from agt_demo.marketplace import init_keypair, sign_catalog

        init_keypair(cfg)
        sign_catalog(cfg)
        print("Done. Public key + catalog are ready; private key is gitignored.")
        return

    if args.marketplace_sign:
        from agt_demo.marketplace import sign_catalog

        sign_catalog(cfg)
        return

    if args.marketplace_tamper:
        from agt_demo.marketplace import tamper_catalog_for_demo

        tamper_catalog_for_demo(cfg)
        print("Next: agent-control-lab --marketplace-enforce  # should reject tools")
        return

    if args.marketplace_enforce:
        cfg.setdefault("marketplace", {})["enforce"] = True

    if args.kill_switch:
        cfg.setdefault("runtime", {})["kill_switch"] = True
        import agt_demo.agt_layers as layers

        layers._RUNTIME_GUARD = None
        get_runtime_guard(cfg)

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
    except MarketplaceRejectedError as e:
        print(f"\nBLOCKED: {e}")
        print("  Fix: agent-control-lab --marketplace-sign")
        print("  Or:  set marketplace.enforce: false")
        sys.exit(3)
    except PermissionError as e:
        print(f"\nBLOCKED: {e}")
        if args.kill_switch:
            print("  Kill switch was engaged — unset and re-run without --kill-switch")
        sys.exit(4)

    print()
    print("DONE")
    print(f"  TTL      : {final.get('ttl_path')}")
    print(f"  Verdict  : {str(final.get('compliance_verdict') or '')[:120]}")
    print(f"  Audit    : {audit_path(cfg)}")
    print(f"  Events   : {events_path(cfg)}")
    print(f"  SRE      : {sre_state_path(cfg)}")
    print(
        f"  Evidence : {repo_root() / cfg.get('artifacts', {}).get('compliance_evidence', 'output/compliance_evidence.json')}"
    )
    print("  Dashboard: streamlit run dashboards/companion_app.py --server.port 8502")


if __name__ == "__main__":
    main()
