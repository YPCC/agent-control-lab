"""OpenTelemetry + structured event emission."""
from __future__ import annotations
import json, logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("agt_demo.telemetry")
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    _OTEL = True
except ImportError:
    _OTEL = False
    trace = None

_initialized = False
_events_path: Optional[Path] = None

def init_telemetry(service_name: str = "agent-control-lab", events_file: Optional[Path] = None, console: bool = False) -> None:
    global _initialized, _events_path
    _events_path = events_file
    if events_file:
        events_file.parent.mkdir(parents=True, exist_ok=True)
    if not _OTEL:
        _initialized = True
        return
    if _initialized:
        return
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    if console:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _initialized = True

def get_tracer(name: str = "agt_demo"):
    if _OTEL and _initialized:
        return trace.get_tracer(name)
    return None

def emit_event(event_type: str, *, agent_id: str = "unknown", action: str = "", allowed: Optional[bool] = None, reason: str = "", attributes: Optional[dict[str, Any]] = None) -> None:
    payload = {"event_type": event_type, "agent_id": agent_id, "action": action, "allowed": allowed, "reason": reason, "timestamp": datetime.now(timezone.utc).isoformat(), "attributes": attributes or {}}
    if _events_path:
        try:
            _events_path.parent.mkdir(parents=True, exist_ok=True)
            with open(_events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload) + "\n")
        except OSError as e:
            logger.warning("event bus write failed: %s", e)
    tracer = get_tracer()
    if tracer:
        with tracer.start_as_current_span(f"gov.{event_type}") as span:
            span.set_attribute("agt.agent_id", agent_id)
            span.set_attribute("agt.action", action)
            if allowed is not None:
                span.set_attribute("agt.allowed", allowed)

def emit_phase(phase: str, agent_id: str = "orchestrator", **attrs: Any) -> None:
    emit_event("phase", agent_id=agent_id, action=phase, attributes=attrs)
