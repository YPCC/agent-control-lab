"""Console entry: agent-control-lab / acl"""

from __future__ import annotations

def main() -> None:
    from agt_demo.config import load_config, repo_root
    from agt_demo.governance import audit_path, events_path
    from agt_demo.agents import run_orchestrator

    cfg = load_config()
    for p in (audit_path(cfg), events_path(cfg)):
        if p.exists():
            p.unlink()

    print("=" * 72)
    print("  Agent Control Lab · Spec-driven LangGraph · AGT 7-layer map")
    print("=" * 72)
    print(f"  Config : {repo_root() / 'config' / 'config.yaml'}")
    print()

    final = run_orchestrator(cfg)
    print()
    print("DONE")
    print(f"  TTL     : {final.get('ttl_path')}")
    print(f"  Verdict : {str(final.get('compliance_verdict') or '')[:120]}")
    print(f"  Audit   : {audit_path(cfg)}")
    print(f"  Events  : {events_path(cfg)}")
    print("  Dashboard: streamlit run dashboards/companion_app.py --server.port 8502")


if __name__ == "__main__":
    main()
