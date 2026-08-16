"""Lab projections of the 7 AGT layers (teaching / demos — not full AGT packages)."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from agt_demo.telemetry import emit_event

logger = logging.getLogger("agt_demo.agt_layers")


def layer_agent_os_note() -> str:
    return (
        "Agent OS: every tool call passes check_policy() "
        "(LiteGovernor allow/deny + optional ACS Rego) before execution."
    )


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
    emit_event(
        "mesh_identity",
        agent_id=agent_id,
        attributes={"did": did, "trust_score": score, "tier": tier},
    )
    return ident


RING_FOR_ACTION = {
    "generate_rdf_kg": 2,
    "create_rdf_infographic": 2,
    "validate_rdf": 3,
    "critique_rdf": 3,
    "list_artifacts": 3,
    "read_artifact": 3,
    "compliance_verdict": 2,
    "delete_file": 0,
    "execute_code": 0,
    "shell": 0,
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
    """Persistent SRE projection: success window + circuit breaker across process runs."""

    slo_success_rate: float = 0.99
    max_failures: int = 5
    window: List[bool] = field(default_factory=list)
    circuit_open: bool = False
    path: Optional[Path] = None

    @classmethod
    def load(cls, path: Path, *, max_failures: int = 5, slo: float = 0.99) -> "SreMonitor":
        mon = cls(slo_success_rate=slo, max_failures=max_failures, path=path)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                mon.window = list(data.get("window") or [])[-50:]
                mon.circuit_open = bool(data.get("circuit_open"))
            except Exception as e:
                logger.warning("SRE state load failed: %s", e)
        return mon

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "window": self.window[-50:],
            "circuit_open": self.circuit_open,
            "success_rate": self.success_rate(),
            "error_budget_remaining": self.error_budget_remaining(),
            "max_failures": self.max_failures,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def record(self, success: bool) -> None:
        self.window.append(bool(success))
        self.window = self.window[-50:]
        failures = self.window.count(False)
        if failures >= self.max_failures:
            if not self.circuit_open:
                print(
                    f"  [SRE] CIRCUIT OPEN — {failures} failures in window "
                    f"(max={self.max_failures}); subsequent runs blocked until reset"
                )
            self.circuit_open = True
            emit_event(
                "sre_circuit_open",
                allowed=False,
                reason=f"failures={failures}",
                attributes={"window": len(self.window)},
            )
        self.save()

    def success_rate(self) -> float:
        if not self.window:
            return 1.0
        return self.window.count(True) / len(self.window)

    def error_budget_remaining(self) -> float:
        target_fail = 1.0 - self.slo_success_rate
        actual_fail = 1.0 - self.success_rate()
        if target_fail <= 0:
            return 0.0
        return max(0.0, 1.0 - (actual_fail / target_fail))

    def reset(self) -> None:
        self.window = []
        self.circuit_open = False
        self.save()
        print("  [SRE] state reset — circuit closed")


def sre_state_path(cfg: Optional[dict] = None) -> Path:
    from agt_demo.config import repo_root

    out = (cfg or {}).get("artifacts", {}).get("output_dir", "output")
    return repo_root() / out / "sre_state.json"


OWASP_AGENTIC = [
    "ASI-01 Goal hijacking",
    "ASI-02 Tool misuse",
    "ASI-03 Identity abuse",
    "ASI-04 Supply chain",
    "ASI-05 Code execution",
    "ASI-06 Memory poisoning",
    "ASI-07 Insecure communication",
    "ASI-08 Cascading failures",
    "ASI-09 Human-agent trust",
    "ASI-10 Rogue agents",
]


def compliance_evidence(audit_denied_actions: List[str]) -> Dict[str, Any]:
    evidence = {k: "not_observed" for k in OWASP_AGENTIC}
    for a in audit_denied_actions:
        if a in ("delete_file", "shell", "execute_code"):
            evidence["ASI-02 Tool misuse"] = "controlled_deny"
            evidence["ASI-05 Code execution"] = "controlled_deny"
        if a == "send_email":
            evidence["ASI-07 Insecure communication"] = "controlled_deny"
    emit_event(
        "compliance_evidence",
        attributes={
            "rows": len(evidence),
            "controlled": sum(1 for v in evidence.values() if v == "controlled_deny"),
        },
    )
    return evidence


@dataclass
class MarketplaceTool:
    name: str
    trust_tier: str  # catalogued | community | unknown
    fingerprint: str  # deterministic hash — NOT a cryptographic signature


def marketplace_catalog(tool_names: List[str]) -> List[MarketplaceTool]:
    """Marketplace projection: fingerprints and trust labels (not Ed25519 signing)."""
    catalogued = {
        "generate_rdf_kg",
        "validate_rdf",
        "create_rdf_infographic",
        "critique_rdf",
        "list_artifacts",
        "read_artifact",
        "compliance_verdict",
    }
    out: List[MarketplaceTool] = []
    for n in tool_names:
        tier = "catalogued" if n in catalogued else "unknown"
        fp = hashlib.sha256(f"acl-tool-manifest:{n}".encode()).hexdigest()[:16]
        out.append(MarketplaceTool(name=n, trust_tier=tier, fingerprint=fp))
    emit_event(
        "marketplace_catalog",
        attributes={
            "tools": len(out),
            "catalogued": sum(1 for t in out if t.trust_tier == "catalogued"),
        },
    )
    print(
        f"  [Marketplace] {len(out)} tools — "
        f"{sum(1 for t in out if t.trust_tier == 'catalogued')} catalogued "
        f"(fingerprints, not crypto signatures)"
    )
    return out


def layer_agent_lightning_note() -> str:
    return (
        "Agent Lightning governs RL *training*. "
        "This lab is a *runtime* control plane; Lightning is architectural reference only."
    )


def print_seven_layer_banner() -> None:
    print("-" * 72)
    print("  AGT 7-layer map (integrations + lab projections)")
    print("-" * 72)
    layers = [
        ("1 Agent OS", "Integrated: LiteGovernor + ACS mediation / host enforce"),
        ("2 Agent Mesh", "Projected: did:acl + trust tiers (not crypto Mesh)"),
        ("3 Agent Runtime", "Partial: privilege rings + kill switch"),
        ("4 Agent SRE", "Partial: persistent window + circuit breaker"),
        ("5 Agent Compliance", "Illustrative: GO/NO-GO + light OWASP map"),
        ("6 Agent Marketplace", "Projected: fingerprints + trust labels"),
        ("7 Agent Lightning", layer_agent_lightning_note()),
    ]
    for title, note in layers:
        print(f"  {title:20s}  {note[:64]}")
    print("-" * 72)
