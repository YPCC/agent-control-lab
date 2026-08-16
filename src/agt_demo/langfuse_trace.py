"""Optional Langfuse tracing. No-op without LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY."""
from __future__ import annotations
import logging, os
from contextlib import contextmanager
from typing import Any, Generator, Optional

logger = logging.getLogger("agt_demo.langfuse")
_client = None
_enabled = False

def init_langfuse() -> bool:
    global _client, _enabled
    pk = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
    sk = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip()
    if not pk or not sk:
        _enabled = False
        return False
    try:
        from langfuse import Langfuse
        _client = Langfuse(public_key=pk, secret_key=sk, host=host)
        _enabled = True
        print(f"[langfuse] enabled → {host}")
        return True
    except Exception as e:
        logger.warning("Langfuse init failed: %s", e)
        _enabled = False
        return False

def is_enabled() -> bool:
    return _enabled and _client is not None

@contextmanager
def trace_run(name: str = "agent-control-lab", session_id: Optional[str] = None, metadata: Optional[dict] = None) -> Generator[Any, None, None]:
    if not is_enabled():
        yield None
        return
    try:
        trace = _client.trace(name=name, session_id=session_id, metadata=metadata or {})
        yield trace
        _client.flush()
    except Exception as e:
        logger.debug("langfuse trace_run error: %s", e)
        yield None

def log_event(trace: Any, name: str, metadata: Optional[dict] = None, level: str = "DEFAULT") -> None:
    if not is_enabled() or trace is None:
        return
    try:
        trace.event(name=name, metadata=metadata or {}, level=level)
    except Exception as e:
        logger.debug("langfuse event error: %s", e)

def score(trace: Any, name: str, value: float, comment: str = "") -> None:
    if not is_enabled() or trace is None:
        return
    try:
        trace.score(name=name, value=value, comment=comment)
    except Exception as e:
        logger.debug("langfuse score error: %s", e)
