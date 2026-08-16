"""Knowledge agent — generate RDF + HTML under governance."""
from __future__ import annotations
from typing import Any, Dict, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated, TypedDict
from agt_demo.config import resolve_llm
from agt_demo.governance import build_governor
from agt_demo.tools.rdf_tools import build_knowledge_tools

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

SYSTEM = "You are a governed RDF Knowledge Agent. Use tools. Refuse destructive actions."

def build_knowledge_graph(cfg: dict[str, Any], agent_spec=None):
    agent_id = (agent_spec or {}).get("id") or cfg.get("agent", {}).get("id", "knowledge")
    gov = (agent_spec or {}).get("governance") or cfg.get("governance", {})
    governor = build_governor(cfg, override={"allow": gov.get("allow"), "deny": gov.get("deny")} if gov.get("allow") else None)
    tools = build_knowledge_tools(cfg, governor, agent_id=agent_id)
    llm, provider = resolve_llm(cfg)
    print(f"[knowledge-agent] LLM provider={provider}  tools={len(tools)}")
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

def run_knowledge_agent(cfg, user_text=None, agent_spec=None):
    compiled, tools, provider = build_knowledge_graph(cfg, agent_spec=agent_spec)
    if provider == "mock":
        print("[knowledge-agent] Mock provider → explicit tool sequence")
        by = {t.name: t for t in tools}
        results = []
        slug = cfg.get("artifacts", {}).get("default_slug", "agt-demo")
        for name, args in [
            ("generate_rdf_kg", {"text": user_text or "", "slug": slug}),
            ("validate_rdf", {"ttl_path": f"{slug}-kg.ttl"}),
            ("create_rdf_infographic", {"ttl_path": f"{slug}-kg.ttl"}),
            ("list_artifacts", {}),
        ]:
            results.append(by[name].invoke(args))
            print(results[-1])
        try:
            by["delete_file"].invoke({"path": "should-be-blocked"})
        except Exception as e:
            print(f"  Caught expected deny: {e}")
        return results
    print("[knowledge-agent] Live provider → LangGraph tool-calling loop")
    prompt = user_text or "Generate an RDF knowledge graph about Agent Governance Toolkit, validate it, and create an HTML explorer."
    final = compiled.invoke({"messages": [HumanMessage(content=prompt)]}, config={"recursion_limit": 12})
    return final["messages"]
