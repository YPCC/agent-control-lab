"""Critic agent — validate + grade RDF under stricter policy."""
from __future__ import annotations
from typing import Any, Dict, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated, TypedDict
from agt_demo.config import resolve_llm
from agt_demo.governance import build_governor
from agt_demo.tools.rdf_tools import build_critic_tools

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

SYSTEM = "You are a strict RDF Critic. Validate and critique only. Do not generate RDF."

def build_critic_graph(cfg, agent_spec=None):
    agent_id = (agent_spec or {}).get("id") or cfg.get("critic", {}).get("id", "critic")
    gov = (agent_spec or {}).get("governance") or cfg.get("critic", {})
    governor = build_governor(cfg, override={
        "allow": gov.get("allow") or ["validate_rdf", "critique_rdf", "list_artifacts", "read_artifact"],
        "deny": gov.get("deny") or ["generate_rdf_kg", "create_rdf_infographic", "delete_file", "execute_code", "shell"],
    })
    tools = build_critic_tools(cfg, governor, agent_id=agent_id)
    llm, provider = resolve_llm(cfg)
    print(f"[critic-agent] LLM provider={provider}  tools={len(tools)}")
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

def run_critic_agent(cfg, ttl_path=None, agent_spec=None):
    compiled, tools, provider = build_critic_graph(cfg, agent_spec=agent_spec)
    slug = cfg.get("artifacts", {}).get("default_slug", "agt-demo")
    ttl = ttl_path or f"{slug}-kg.ttl"
    if provider == "mock":
        print("[critic-agent] Mock provider → explicit critique sequence")
        by = {t.name: t for t in tools}
        results = []
        results.append(by["validate_rdf"].invoke({"ttl_path": ttl}))
        print(results[-1])
        results.append(by["critique_rdf"].invoke({"ttl_path": ttl}))
        print(results[-1])
        results.append(by["list_artifacts"].invoke({}))
        print(results[-1])
        return results
    print("[critic-agent] Live provider → LangGraph tool-calling loop")
    final = compiled.invoke(
        {"messages": [HumanMessage(content=f"Validate and critique {ttl}. List artifacts.")]},
        config={"recursion_limit": 8},
    )
    return final["messages"]
