# Agent Control Lab

**Package / GitHub:** [`YPCC/agent-control-lab`](https://github.com/YPCC/agent-control-lab)

A **spec-driven LangGraph multi-agent control plane** that makes **Agent Governance Toolkit (AGT)** concepts visible inside a real application loop — not a reimplementation of Microsoft’s seven packages.

> **Positioning:** seven-layer AGT **concept map**, with **selected runtime integrations** and **lab projections**.  
> See [docs/AGT_SEVEN_LAYERS.md](docs/AGT_SEVEN_LAYERS.md).

Upstream: [Introducing the Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)

---

## Architecture

Agent Control Lab has **two architectural planes**: an **agent execution plane** and a **governance / control plane**.

> Agent Control Lab separates agent execution from agent governance: **LangGraph** determines *what* agents do and in *what sequence*, while a surrounding **control plane** mediates policy, identity, privilege, reliability, compliance, tool trust, audit, and observability.

| Plane | Responsibility |
|-------|----------------|
| **Agent execution plane** | Spec-driven LangGraph workflow: `knowledge → critic → compliance` |
| **Governance control plane** | Policy mediation, identity/trust, runtime rings + kill switch, SRE circuit, marketplace trust, audit/telemetry |

![C4 context, container, and 7-layer AGT concept map](docs/architecture/c4-and-seven-layer-map.jpg)

*Figure: (1) C4 context — developer ↔ lab ↔ LLM providers, Microsoft AGT, Langfuse. (2) C4 container — specification layer, orchestrator, execution agents, and governance control plane. (3) Logical 7-layer concept map over the multi-agent workflow.*

### Execution plane (LangGraph)

```text
USER TASK
    │
    ▼
SRE circuit check ──(open?)──► BLOCK
    │
    ▼
Knowledge Agent  →  Critic Agent  →  Compliance Agent  →  GO / NO-GO
    │                     │                  │
    └──────────── audit & telemetry ─────────┘
```

Specs live in `config/agents/*.yaml` and `config/graphs/default.yaml`. The orchestrator builds the `StateGraph` from those specs at runtime.

### Governance control plane

Wired **around** tool calls (not instead of the graph):

| Capability | Status | Mechanism |
|------------|--------|-----------|
| Policy mediation | **Integrated** | LiteGovernor + optional ACS at `PRE_TOOL_CALL`; host enforces |
| Identity / trust | **Projected** | `did:acl:…` + trust tiers |
| Runtime | **Partial** | Privilege rings + kill switch (`--kill-switch`) |
| SRE | **Partial** | Persistent window + circuit (`--sre-demo`) |
| Compliance | **Illustrative** | GO/NO-GO + `output/compliance_evidence.json` |
| Marketplace | **Projected** | Fingerprints + optional Ed25519 verify |
| Lightning | **Reference only** | Training-time boundary (out of scope) |

Enforcement order on every tool call:

```text
RuntimeGuard → LiteGovernor → optional ACS (evaluate) → host PermissionError if denied
```

Further detail: [docs/architecture/README.md](docs/architecture/README.md) · [docs/AGT_SEVEN_LAYERS.md](docs/AGT_SEVEN_LAYERS.md)

---

## Cite this repository

If you use **Agent Control Lab** in a paper, talk, course, or product evaluation, please cite:

### BibTeX

```bibtex
@software{agent_control_lab,
  title        = {Agent Control Lab: Spec-driven LangGraph control plane for AGT concept demos},
  author       = {{Agent Control Lab Contributors}},
  year         = {2026},
  url          = {https://github.com/YPCC/agent-control-lab},
  note         = {Lab projections of Microsoft Agent Governance Toolkit concepts}
}
```

### APA-style

> Agent Control Lab Contributors. (2026). *Agent Control Lab: Spec-driven LangGraph control plane for AGT concept demos* [Computer software]. https://github.com/YPCC/agent-control-lab

### Inline

> …using the open-source Agent Control Lab control-plane demo (https://github.com/YPCC/agent-control-lab).

Please also cite Microsoft’s AGT when discussing the upstream architecture:

> Microsoft. (2026). *Introducing the Agent Governance Toolkit*. https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/

---

## What this lab is (and is not)

| Primary claims | Status |
|----------------|--------|
| Spec-driven LangGraph workflow (`knowledge → critic → compliance`) | **Real** |
| ACS / LiteGovernor policy mediation on tool calls + host enforcement + audit | **Integrated** |
| Runtime kill switch + rings wired into `check_policy` | **Partial** |
| Persistent SRE circuit breaker | **Partial** |
| Audit → OWASP evidence JSON | **Illustrative** |
| Marketplace fingerprints + optional Ed25519 verify | **Projected** |
| Full Microsoft AGT monorepo (Mesh crypto, Hypervisor, Lightning RL, …) | **Out of scope** |

### AGT concept map

| AGT concept | Status in Agent Control Lab |
|-------------|----------------------------|
| **Agent OS / ACS** | **Integrated** — RuntimeGuard → LiteGovernor → optional ACS; host enforces |
| **Agent Mesh** | **Projected** — `did:acl:…` + trust tiers |
| **Agent Runtime** | **Partial** — rings + kill switch (`--kill-switch` / `AGT_KILL_SWITCH`) |
| **Agent SRE** | **Partial** — `output/sre_state.json` + `--sre-demo` |
| **Agent Compliance** | **Illustrative** — GO/NO-GO + `output/compliance_evidence.json` |
| **Agent Marketplace** | **Projected** — fingerprints; optional Ed25519 (`--marketplace-init`) |
| **Agent Lightning** | **Reference only** |

---

## Default interaction graph

```text
knowledge → critic → compliance → END
```

| Agent | Role | Spec |
|-------|------|------|
| **knowledge** | Generate RDF + HTML explorer | `config/agents/knowledge.yaml` |
| **critic** | Validate & grade quality | `config/agents/critic.yaml` |
| **compliance** | Final GO / NO-GO gate | `config/agents/compliance.yaml` |

Graph: `config/graphs/default.yaml` · Extend: [docs/ADDING_AGENTS.md](docs/ADDING_AGENTS.md)

---

## Quick start

```bash
git clone https://github.com/YPCC/agent-control-lab.git
cd agent-control-lab
bash scripts/setup_uv.sh
source .venv/bin/activate

# Optional LLM keys (else mock)
# export XAI_API_KEY=...   # or OPENAI_API_KEY / GOOGLE_API_KEY

agent-control-lab          # or: acl
```

Baseline run is unchanged: governance allow/deny, RDF artifacts, audit JSONL, companion dashboard.

### Additive demos (optional)

Full detail: [docs/RUNTIME_MARKETPLACE_COMPLIANCE.md](docs/RUNTIME_MARKETPLACE_COMPLIANCE.md)

**SRE circuit**

```bash
agent-control-lab --sre-reset
agent-control-lab --sre-demo    # repeat until CIRCUIT OPEN
agent-control-lab               # blocked
agent-control-lab --sre-reset
```

**Runtime kill switch**

```bash
agent-control-lab --kill-switch
# or: AGT_KILL_SWITCH=1 agent-control-lab
```

**Compliance evidence** (written every completed orchestration)

```bash
agent-control-lab
cat output/compliance_evidence.json
```

**Marketplace Ed25519**

```bash
agent-control-lab --marketplace-init      # keys + signed catalog
agent-control-lab --marketplace-tamper
agent-control-lab --marketplace-enforce   # should reject
agent-control-lab --marketplace-sign      # restore
```

Default `marketplace.enforce: false` keeps older demos intact.

### Dashboards

```bash
streamlit run dashboards/companion_app.py --server.port 8502
bash scripts/launch_official_dashboard.sh
```

### Langfuse (optional)

```bash
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
export LANGFUSE_HOST=https://cloud.langfuse.com
agent-control-lab
```

---

## Documentation

| Doc | Topic |
|-----|--------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | First run |
| [docs/architecture/README.md](docs/architecture/README.md) | Two-plane architecture + C4 figure |
| [docs/AGT_SEVEN_LAYERS.md](docs/AGT_SEVEN_LAYERS.md) | Honest 7-layer map |
| [docs/RUNTIME_MARKETPLACE_COMPLIANCE.md](docs/RUNTIME_MARKETPLACE_COMPLIANCE.md) | Kill switch, evidence, Ed25519 |
| [docs/ADDING_AGENTS.md](docs/ADDING_AGENTS.md) | Spec-driven agents |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Providers, env vars |

---

## License

MIT (lab code). Upstream [Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) is Microsoft MIT open source.
