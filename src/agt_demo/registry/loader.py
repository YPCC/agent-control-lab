"""Spec-driven agent registry and graph loader."""
from __future__ import annotations
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import yaml
from agt_demo.config import repo_root

@dataclass
class AgentSpec:
    id: str
    name: str
    description: str
    role: str
    governance: dict
    tools: List[str]
    runtime_module: str
    runtime_build: str
    runtime_run: str
    system_prompt: str
    raw: dict = field(default_factory=dict)
    def load_run_callable(self) -> Callable:
        return getattr(importlib.import_module(self.runtime_module), self.runtime_run)
    def load_build_callable(self) -> Optional[Callable]:
        return getattr(importlib.import_module(self.runtime_module), self.runtime_build, None)

@dataclass
class GraphSpec:
    id: str
    name: str
    entry: str
    nodes: List[dict]
    edges: List[dict]
    state_keys: List[str]
    raw: dict = field(default_factory=dict)

def _agents_dir(cfg=None):
    return repo_root() / (cfg or {}).get("agents_dir", "config/agents")

def _graphs_dir(cfg=None):
    return repo_root() / (cfg or {}).get("graphs_dir", "config/graphs")

def _parse_agent(doc, path):
    md = doc.get("metadata") or {}
    sp = doc.get("spec") or {}
    rt = sp.get("runtime") or {}
    return AgentSpec(
        id=str(md["id"]), name=str(md.get("name") or md["id"]),
        description=str(md.get("description") or ""), role=str(sp.get("role") or "worker"),
        governance=dict(sp.get("governance") or {}), tools=list(sp.get("tools") or []),
        runtime_module=str(rt["module"]), runtime_build=str(rt.get("build") or ""),
        runtime_run=str(rt["run"]), system_prompt=str(sp.get("system_prompt") or ""), raw=doc,
    )

class AgentRegistry:
    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self._by_id: Dict[str, AgentSpec] = {}
        self.reload()
    def reload(self):
        self._by_id.clear()
        d = _agents_dir(self.cfg)
        if not d.exists():
            return
        for path in sorted(d.glob("*.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if not doc:
                continue
            spec = _parse_agent(doc, path)
            self._by_id[spec.id] = spec
    def get(self, agent_id: str) -> AgentSpec:
        if agent_id not in self._by_id:
            raise KeyError(f"Unknown agent '{agent_id}'. Known: {list(self._by_id)}")
        return self._by_id[agent_id]
    def all(self):
        return list(self._by_id.values())
    def ids(self):
        return list(self._by_id.keys())
    def summary(self):
        return [{"id": a.id, "name": a.name, "role": a.role, "tools": a.tools,
                 "allow": (a.governance.get("allow") or [])[:6]} for a in self.all()]

def load_graph_spec(name="default", cfg=None) -> GraphSpec:
    path = _graphs_dir(cfg) / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Graph spec not found: {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    md, sp = doc.get("metadata") or {}, doc.get("spec") or {}
    return GraphSpec(
        id=str(md.get("id") or name), name=str(md.get("name") or name),
        entry=str(sp.get("entry") or ""), nodes=list(sp.get("nodes") or []),
        edges=list(sp.get("edges") or []), state_keys=list(sp.get("state") or []), raw=doc,
    )
