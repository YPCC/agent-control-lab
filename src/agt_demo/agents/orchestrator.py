"""Spec-driven parent LangGraph for Agent Control Lab."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict
from agt_demo.config import resolve_llm
from agt_demo.governance import events_path, try_load_acs
from agt_demo.registry import AgentRegistry, load_graph_spec
from agt_demo.telemetry import emit_phase, init_telemetry
from agt_demo.langfuse_trace import init_langfuse, trace_run, log_event, score
from agt_demo.agt_layers import mesh_identity, print_seven_layer_banner, marketplace_catalog, SreMonitor

class OrchestratorState(TypedDict, total=False):
    cfg: dict
    user_text: Optional[str]
    ttl_path: Optional[str]
    critique_summary: Optional[str]
    compliance_verdict: Optional[str]
    agent_results: dict
    provider: str
    error: Optional[str]

def _make_node(agent_id: str, registry: AgentRegistry):
    def node_fn(state: OrchestratorState) -> Dict:
        cfg = state["cfg"]
        spec = registry.get(agent_id)
        emit_phase(f"{agent_id}_start", agent_id=spec.id)
        mesh_identity(spec.id)
        run_fn = spec.load_run_callable()
        agent_meta = {"id": spec.id, "name": spec.name, "governance": spec.governance, "system_prompt": spec.system_prompt}
        results: List = []
        updates: Dict[str, Any] = {}
        if agent_id == "knowledge":
            results = run_fn(cfg, user_text=state.get("user_text"))
            slug = cfg.get("artifacts", {}).get("default_slug", "agt-demo")
            updates["ttl_path"] = f"{slug}-kg.ttl"
        elif agent_id == "critic":
            results = run_fn(cfg, ttl_path=state.get("ttl_path"))
            updates["critique_summary"] = results[-1] if results and isinstance(results[-1], str) else str(results[-1] if results else "")
        elif agent_id == "compliance":
            try:
                results = run_fn(cfg, ttl_path=state.get("ttl_path"), agent_spec=agent_meta)
            except TypeError:
                results = run_fn(cfg, ttl_path=state.get("ttl_path"))
            updates["compliance_verdict"] = results[-1] if results and isinstance(results[-1], str) else str(results[-1] if results else "")
        else:
            try:
                results = run_fn(cfg, ttl_path=state.get("ttl_path"), agent_spec=agent_meta)
            except TypeError:
                try:
                    results = run_fn(cfg, ttl_path=state.get("ttl_path"))
                except TypeError:
                    results = run_fn(cfg)
        ar = dict(state.get("agent_results") or {})
        ar[agent_id] = results if isinstance(results, list) else [results]
        updates["agent_results"] = ar
        emit_phase(f"{agent_id}_done", agent_id=spec.id)
        return updates
    node_fn.__name__ = f"node_{agent_id}"
    return node_fn

def build_orchestrator_from_specs(cfg: dict[str, Any], graph_name: str = "default"):
    registry = AgentRegistry(cfg)
    graph_spec = load_graph_spec(graph_name, cfg)
    print(f"[orchestrator] graph={graph_spec.id!r}  agents={registry.ids()}")
    for row in registry.summary():
        print(f"  · {row['id']:12s} role={row['role']:10s} tools={row['tools']}")
    agent_ids = set(registry.ids())
    for n in graph_spec.nodes:
        aid = n.get("agent") or n.get("id")
        if aid not in agent_ids:
            raise KeyError(f"Graph node references unknown agent '{aid}'")
    sg = StateGraph(OrchestratorState)
    node_ids = []
    for n in graph_spec.nodes:
        node_id = n.get("id") or n.get("agent")
        agent_id = n.get("agent") or n.get("id")
        sg.add_node(node_id, _make_node(agent_id, registry))
        node_ids.append(node_id)
    sg.set_entry_point(graph_spec.entry or node_ids[0])
    for e in graph_spec.edges:
        src, dst = e["from"], e["to"]
        sg.add_edge(src, END if dst in ("__end__", "END", "end") else dst)
    return sg.compile(), registry, graph_spec

def run_orchestrator(cfg: dict[str, Any], user_text: Optional[str] = None, graph_name: str = "default") -> OrchestratorState:
    init_telemetry(service_name="agent-control-lab", events_file=events_path(cfg), console=False)
    init_langfuse()
    print_seven_layer_banner()
    acs = try_load_acs(cfg)
    cfg = {**cfg, "_acs": acs}
    _, provider = resolve_llm(cfg)
    print(f"[orchestrator] provider={provider}  acs={'yes' if acs else 'no'}")
    emit_phase("orchestrator_start", provider=provider, acs=bool(acs))
    compiled, registry, graph_spec = build_orchestrator_from_specs(cfg, graph_name)
    all_tools = sorted({t for a in registry.all() for t in a.tools})
    marketplace_catalog(all_tools)
    sre = SreMonitor()
    with trace_run(name="agent-control-lab-run", metadata={"graph": graph_spec.id, "provider": provider, "agents": registry.ids()}) as lf_trace:
        log_event(lf_trace, "orchestrator_start", {"graph": graph_spec.id})
        final: OrchestratorState = compiled.invoke({"cfg": cfg, "user_text": user_text, "provider": provider, "agent_results": {}})
        verdict = final.get("compliance_verdict") or ""
        ok = "GO" in verdict and "NO-GO" not in verdict
        sre.record(ok)
        log_event(lf_trace, "orchestrator_done", {"verdict": str(verdict)[:200]})
        score(lf_trace, "pipeline_success", 1.0 if ok else 0.0)
        emit_phase("orchestrator_done", graph=graph_spec.id)
    final["provider"] = provider
    return final
