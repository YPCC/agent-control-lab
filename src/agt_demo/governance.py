"""Dual-path governance: RuntimeGuard → LiteGovernor → optional ACS; host enforces."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from agent_os.lite import govern, LiteGovernor

from agt_demo.telemetry import emit_event

logger = logging.getLogger("agt_demo.governance")

try:
    from agent_control_specification import (
        AgentControl,
        EnforcementMode,
        InterventionPoint,
        JsonStdoutTelemetrySink,
    )

    _HAS_ACS = True
except ImportError:
    _HAS_ACS = False
    AgentControl = None  # type: ignore


def build_governor(cfg: dict[str, Any], override: Optional[dict] = None) -> LiteGovernor:
    gcfg = dict(cfg.get("governance", {}))
    if override:
        for k in ("allow", "deny", "deny_patterns", "blocked_content", "max_calls"):
            if k in override:
                gcfg[k] = override[k]
    return govern(
        allow=gcfg.get("allow"),
        deny=gcfg.get("deny"),
        deny_patterns=gcfg.get("deny_patterns"),
        blocked_content=gcfg.get("blocked_content"),
        max_calls=gcfg.get("max_calls", 50),
        log=True,
    )


def audit_path(cfg: dict[str, Any]) -> Path:
    from agt_demo.config import repo_root

    p = repo_root() / cfg.get("governance", {}).get(
        "audit_log", "output/governance_audit.jsonl"
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def events_path(cfg: dict[str, Any]) -> Path:
    from agt_demo.config import repo_root

    p = repo_root() / cfg.get("governance", {}).get(
        "events_log", "output/governance_events.jsonl"
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def append_audit(
    cfg: dict,
    action: str,
    allowed: bool,
    reason: str,
    agent_id: str = "unknown",
    layer: str = "policy",
) -> None:
    entry = {
        "action": action,
        "allowed": allowed,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent_id,
        "layer": layer,
    }
    with open(audit_path(cfg), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_policy(
    governor: LiteGovernor,
    cfg: dict[str, Any],
    action_name: str,
    agent_id: str = "unknown",
    acs: Any = None,
) -> None:
    """Enforcement order: RuntimeGuard → LiteGovernor → optional ACS. Host raises."""
    from agt_demo.agt_layers import get_runtime_guard

    guard = get_runtime_guard(cfg)
    ok, rt_reason = guard.allow(action_name)
    if not ok:
        reason = f"RuntimeDenied: {rt_reason}"
        append_audit(cfg, action_name, False, reason, agent_id=agent_id, layer="runtime")
        emit_event(
            "policy_decision",
            agent_id=agent_id,
            action=action_name,
            allowed=False,
            reason=reason,
            attributes={"layer": "runtime"},
        )
        print(f"  [Runtime] BLOCKED → {action_name}  ({agent_id})  {rt_reason}")
        raise PermissionError(
            f"RuntimeDenied: action '{action_name}' is not permitted. reason={reason}"
        )

    allowed = governor.is_allowed(action_name)
    reason = "Allowed by policy" if allowed else "Action denied by policy"
    if governor.audit_trail:
        last = governor.audit_trail[-1]
        reason = getattr(last, "reason", reason) or reason

    acs_note = ""
    if acs is not None and _HAS_ACS:
        try:
            snapshot = {
                "tool_call": {"name": action_name, "args": {}},
                "tool_name": action_name,
                "envelope": {"agent_id": agent_id, "tool_name": action_name},
            }

            async def _eval():
                return await acs.evaluate_intervention_point(
                    InterventionPoint.PRE_TOOL_CALL,
                    snapshot,
                    mode=EnforcementMode.EVALUATE_ONLY,
                )

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                raise RuntimeError("acs_skip_running_loop")
            result = asyncio.run(_eval())
            verdict = getattr(result, "verdict", None) or result
            reason_s = str(getattr(verdict, "reason", "") or "")
            if reason_s.startswith("runtime_error:"):
                acs_note = f" [ACS:runtime_skip:{reason_s}]"
            else:
                decision = getattr(verdict, "decision", None)
                permits = (
                    "allow" in str(decision).lower() if decision is not None else True
                )
                if not permits:
                    allowed = False
                    acs_note = " [ACS:deny]"
                else:
                    acs_note = " [ACS:allow]"
                reason = f"{reason}{acs_note}"
        except Exception as e:
            logger.debug("ACS evaluation skipped: %s", e)
            acs_note = f" [ACS:error:{type(e).__name__}]"

    append_audit(
        cfg, action_name, allowed, reason, agent_id=agent_id, layer="policy"
    )
    emit_event(
        "policy_decision",
        agent_id=agent_id,
        action=action_name,
        allowed=allowed,
        reason=reason,
        attributes={"acs": bool(acs), "acs_note": acs_note.strip(), "layer": "policy"},
    )
    if not allowed:
        print(f"  [GOVERNANCE] BLOCKED → {action_name}  ({agent_id})")
        raise PermissionError(
            f"GovernanceDenied: action '{action_name}' is not permitted. reason={reason}"
        )
    print(f"  [GOVERNANCE] ALLOWED → {action_name}  ({agent_id})")


def try_load_acs(cfg: dict[str, Any]):
    if not _HAS_ACS:
        return None
    from agt_demo.config import repo_root

    path = repo_root() / cfg.get("governance", {}).get(
        "acs_manifest", "policies/acs_manifest.yaml"
    )
    if not path.exists():
        return None
    try:
        sinks = None
        try:
            sinks = [JsonStdoutTelemetrySink()]
        except Exception:
            pass
        runtime = AgentControl.from_path(str(path), telemetry_sink=sinks)
        print(f"[governance] ACS AgentControl loaded ← {path.name}")
        return runtime
    except Exception as e:
        print(f"[governance] ACS unavailable ({type(e).__name__}); LiteGovernor only")
        return None
