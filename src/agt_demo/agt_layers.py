"""Lab projections of the 7 AGT layers."""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List
from agt_demo.telemetry import emit_event

def layer_agent_os_note() -> str:
    return "Agent OS: every tool call passes check_policy() (LiteGovernor + optional ACS Rego)."

@dataclass
class MeshIdentity:
    agent_id: str
    did: str
    trust_score: int
    tier: str

_TIER = [(800, "high"), (600, "elevated"), (400, "standard"), (200, "low"), (0, "untrusted")]

def mesh_identity(agent_id: str, base_score: int = 750) -> MeshIdentity:
    digest = hashlib.sha256(agent_id.encode()).hexdigest()[:16]
    did = f"did:acl:{digest}"
    score = max(0, min(1000, base_score))
    tier = next(t for threshold, t in _TIER if score >= threshold)
    ident = MeshIdentity(agent_id=agent_id, did=did, trust_score=score, tier=tier)
    emit_event("mesh_identity", agent_id=agent_id, attributes={"did": did, "trust_score": score, "tier": tier})
    return ident

RING_FOR_ACTION = {
    "generate_rdf_kg": 2, "create_rdf_infographic": 2, "validate_rdf": 3, "critique_rdf": 3,
    "list_artifacts": 3, "read_artifact": 3, "compliance_verdict": 2,
    "delete_file": 0, "execute_code": 0, "shell": 0,
}

@dataclass
class RuntimeGuard:
    max_ring: int = 2
    killed: bool = False
    def allow(self, action: str) -> bool:
        if self.killed:
            return False
        need = RING_FOR_ACTION.get(action, 2)
        if need == 0:
            return False
        return True
    def kill(self, reason: str = "operator") -> None:
        self.killed = True
        emit_event("runtime_kill_switch", action=reason, allowed=False, reason=reason)

@dataclass
class SreMonitor:
    slo_success_rate: float = 0.99
    window: List[bool] = field(default_factory=list)
    circuit_open: bool = False
    max_failures: int = 5
    def record(self, success: bool) -> None:
        self.window.append(success)
        self.window = self.window[-50:]
        if self.window.count(False) >= self.max_failures:
            self.circuit_open = True
            emit_event("sre_circuit_open", allowed=False, reason="max_failures")
    def success_rate(self) -> float:
        return 1.0 if not self.window else self.window.count(True) / len(self.window)

OWASP_AGENTIC = [
    "ASI-01 Goal hijacking", "ASI-02 Tool misuse", "ASI-03 Identity abuse",
    "ASI-04 Supply chain", "ASI-05 Code execution", "ASI-06 Memory poisoning",
    "ASI-07 Insecure communication", "ASI-08 Cascading failures",
    "ASI-09 Human-agent trust", "ASI-10 Rogue agents",
]

def compliance_evidence(audit_denied_actions: List[str]) -> Dict[str, Any]:
    evidence = {k: "not_observed" for k in OWASP_AGENTIC}
    for a in audit_denied_actions:
        if a in ("delete_file", "shell", "execute_code"):
            evidence["ASI-02 Tool misuse"] = "controlled_deny"
            evidence["ASI-05 Code execution"] = "controlled_deny"
    emit_event("compliance_evidence", attributes={"rows": len(evidence)})
    return evidence

@dataclass
class MarketplaceTool:
    name: str
    trust_tier: str
    signature: str

def marketplace_catalog(tool_names: List[str]) -> List[MarketplaceTool]:
    signed = {"generate_rdf_kg", "validate_rdf", "create_rdf_infographic", "critique_rdf",
              "list_artifacts", "read_artifact", "compliance_verdict"}
    out = []
    for n in tool_names:
        tier = "signed" if n in signed else "unknown"
        sig = hashlib.sha256(f"acl-tool:{n}".encode()).hexdigest()[:12]
        out.append(MarketplaceTool(name=n, trust_tier=tier, signature=sig))
    emit_event("marketplace_catalog", attributes={"tools": len(out), "signed": sum(1 for t in out if t.trust_tier == "signed")})
    return out

def layer_agent_lightning_note() -> str:
    return "Agent Lightning governs RL training; this lab is the runtime control plane."

def print_seven_layer_banner() -> None:
    print("-" * 72)
    print("  AGT 7-layer map (lab projections)")
    print("-" * 72)
    layers = [
        ("1 Agent OS", layer_agent_os_note()),
        ("2 Agent Mesh", "DID-style ids + trust score on each agent node"),
        ("3 Agent Runtime", "Privilege rings + kill switch"),
        ("4 Agent SRE", "Success window, error budget, circuit breaker"),
        ("5 Agent Compliance", "OWASP Agentic evidence from audit denials"),
        ("6 Agent Marketplace", "Signed tool catalog / trust tiers"),
        ("7 Agent Lightning", layer_agent_lightning_note()),
    ]
    for title, note in layers:
        print(f"  {title:20s}  {note[:64]}")
    print("-" * 72)
