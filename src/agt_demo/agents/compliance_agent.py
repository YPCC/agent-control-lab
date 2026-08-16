"""Compliance gate agent — final GO / NO-GO."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated, TypedDict
from agt_demo.config import resolve_llm, repo_root
from agt_demo.governance import build_governor, check_policy, audit_path

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

SYSTEM = "You are a Compliance Gate Agent. Emit GO or NO-GO. Do not generate or delete content."

def _output_dir(cfg):
    return repo_root() / cfg.get("artifacts", {}).get("output_dir", "output")

def build_compliance_tools(cfg, governor, agent_id):
    def _check(action):
        check_policy(governor, cfg, action, agent_id=agent_id, acs=cfg.get("_acs"))
    @tool
    def list_artifacts() -> str:
        """List output artifacts."""
        _check("list_artifacts")
        files = sorted(_output_dir(cfg).glob("*"))
        return "\n".join(f"- {f.name}" for f in files) if files else "No artifacts."
    @tool
    def read_artifact(path: str) -> str:
        """Read first 40 lines of an artifact."""
        _check("read_artifact")
        p = Path(path)
        if not p.exists():
            p = _output_dir(cfg) / path
        if not p.exists():
            return f"Not found: {path}"
        return "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[:40])
    @tool
    def compliance_verdict(ttl_path: str = "", notes: str = "") -> str:
        """Emit GO or NO-GO based on artifacts and audit."""
        _check("compliance_verdict")
        out = _output_dir(cfg)
        ttl = Path(ttl_path) if ttl_path else None
        if ttl and not ttl.exists():
            ttl = out / ttl_path
        has_ttl = bool(ttl and ttl.exists())
        has_html = any(out.glob("*-explorer.html"))
        denied = 0
        audit = audit_path(cfg)
        if audit.exists():
            for line in audit.read_text().splitlines():
                if '"allowed": false' in line or '"allowed":false' in line:
                    denied += 1
        if has_ttl and has_html:
            return f"VERDICT: GO\n- Turtle present: {has_ttl}\n- HTML explorer present: {has_html}\n- Policy denials recorded: {denied}\n- Notes: {notes or 'none'}"
        return f"VERDICT: NO-GO\n- Turtle present: {has_ttl}\n- HTML explorer present: {has_html}\n- Notes: {notes or 'missing required artifacts'}"
    return [list_artifacts, read_artifact, compliance_verdict]

def build_compliance_graph(cfg, agent_spec=None):
    agent_id = (agent_spec or {}).get("id") or "compliance"
    gov = (agent_spec or {}).get("governance") or {}
    governor = build_governor(cfg, override={
        "allow": gov.get("allow") or ["list_artifacts", "read_artifact", "compliance_verdict"],
        "deny": gov.get("deny") or ["generate_rdf_kg", "create_rdf_infographic", "delete_file", "execute_code", "shell"],
    })
    tools = build_compliance_tools(cfg, governor, agent_id)
    llm, provider = resolve_llm(cfg)
    print(f"[compliance-agent] LLM provider={provider}  tools={len(tools)}")
    try:
        llm_with_tools = llm.bind_tools(tools)
    except Exception:
        llm_with_tools = llm
    tool_node = ToolNode(tools)
    def agent_node(state: AgentState) -> Dict:
        msgs = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in msgs):
            msgs = [SystemMessage(content=SYSTEM)] + list(msgs)
        return {"messages": [llm_with_tools.invoke(msgs)]}
    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
            return "tools"
        return END
    g = StateGraph(AgentState)
    g.add_node("agent", agent_node)
    g.add_node("tools", tool_node)
    g.set_entry_point("agent")
    g.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    g.add_edge("tools", "agent")
    return g.compile(), tools, provider

def run_compliance_agent(cfg, ttl_path=None, agent_spec=None):
    compiled, tools, provider = build_compliance_graph(cfg, agent_spec=agent_spec)
    slug = cfg.get("artifacts", {}).get("default_slug", "agt-demo")
    ttl = ttl_path or f"{slug}-kg.ttl"
    if provider == "mock":
        print("[compliance-agent] Mock provider → explicit compliance sequence")
        by = {t.name: t for t in tools}
        results = [by["list_artifacts"].invoke({}), by["compliance_verdict"].invoke({"ttl_path": ttl, "notes": "pipeline complete"})]
        for r in results:
            print(r)
        return results
    final = compiled.invoke(
        {"messages": [HumanMessage(content=f"Review artifacts for {ttl}. Call compliance_verdict.")]},
        config={"recursion_limit": 8},
    )
    return final["messages"]
