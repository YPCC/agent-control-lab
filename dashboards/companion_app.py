"""Companion Streamlit dashboard for Agent Control Lab."""
from __future__ import annotations
import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
st.set_page_config(page_title="Agent Control Lab", layout="wide")
st.title("Agent Control Lab — Companion")
st.caption("Policy feed · telemetry · artifacts")

AUDIT = ROOT / "output" / "governance_audit.jsonl"
EVENTS = ROOT / "output" / "governance_events.jsonl"

c1, c2, c3 = st.columns(3)
allowed = denied = 0
if AUDIT.exists():
    for line in AUDIT.read_text().splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            if e.get("allowed"):
                allowed += 1
            else:
                denied += 1
        except Exception:
            pass
c1.metric("Allowed", allowed)
c2.metric("Denied", denied)
c3.metric("Events", sum(1 for _ in EVENTS.open()) if EVENTS.exists() else 0)

st.subheader("Policy audit")
if AUDIT.exists():
    for line in reversed(AUDIT.read_text().splitlines()[-30:]):
        if line.strip():
            try:
                e = json.loads(line)
                icon = "OK" if e.get("allowed") else "BLOCK"
                st.text(f"{icon} {e.get('action')} agent={e.get('agent_id')} {e.get('reason','')[:80]}")
            except Exception:
                st.text(line)
else:
    st.caption("No audit yet — run agent-control-lab")

st.subheader("Artifacts")
out = ROOT / "output"
if out.exists():
    for f in sorted(out.glob("*")):
        st.text(f"{f.name}  ({f.stat().st_size} bytes)")
