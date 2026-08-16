# Agent Control Lab

**Package / GitHub:** [`YPCC/agent-control-lab`](https://github.com/YPCC/agent-control-lab)

A **spec-driven LangGraph multi-agent control plane** that makes **Agent Governance Toolkit (AGT)** concepts visible inside a real application loop — not a reimplementation of Microsoft’s seven packages.

> **Positioning:** seven-layer AGT **concept map**, with **selected runtime integrations** and **lab projections**.  
> See [docs/AGT_SEVEN_LAYERS.md](docs/AGT_SEVEN_LAYERS.md).

Upstream blog: [Introducing the Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)

---

## What this lab is (and is not)

| Primary claims | Status |
|----------------|--------|
| Spec-driven LangGraph workflow (`knowledge → critic → compliance`) | **Real** |
| ACS / LiteGovernor policy mediation on tool calls + host enforcement + audit | **Integrated** |
| Mesh, Runtime, SRE, Marketplace, Compliance as teaching projections | **Projected / partial** |
| Full Microsoft AGT monorepo (Mesh crypto, Hypervisor, Lightning RL, …) | **Out of scope** |

### AGT concept map

| AGT concept | Status in Agent Control Lab |
|-------------|----------------------------|
| **Agent OS / ACS** | **Integrated** — LiteGovernor + optional ACS at `PRE_TOOL_CALL`; host enforces via `PermissionError` |
| **Agent Mesh** | **Projected** — deterministic `did:acl:…` identities and trust tiers (not Ed25519 Mesh) |
| **Agent Runtime** | **Partial** — privilege-ring map + kill-switch helper (not a hypervisor/sandbox) |
| **Agent SRE** | **Partial** — persistent success window, error budget, circuit breaker across runs |
| **Agent Compliance** | **Illustrative** — GO/NO-GO agent + light OWASP Agentic evidence mapping |
| **Agent Marketplace** | **Projected** — tool catalog with **fingerprints** and trust labels (not cryptographic signing) |
| **Agent Lightning** | **Reference only** — training-time counterpart; not implemented in this runtime lab |

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

### SRE circuit demo

State is persisted in `output/sre_state.json` across runs:

```bash
# Normal run records success/failure
agent-control-lab

# Force failures until the circuit opens, then block
agent-control-lab --sre-demo
# or: python scripts/run_demo.py --sre-demo
```

When the circuit is open, subsequent runs refuse the pipeline until you reset:

```bash
agent-control-lab --sre-reset
# or: rm output/sre_state.json
```

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

## How to read the 7-layer hooks

| Layer | What you will actually see |
|-------|----------------------------|
| Agent OS | `[GOVERNANCE] ALLOWED` / `BLOCKED` — LiteGovernor (+ ACS evaluate) before tools |
| Agent Mesh | `did:acl:…` + trust tier events (simulation) |
| Agent Runtime | Destructive tools mapped to ring 0 and denied |
| Agent SRE | `output/sre_state.json`, circuit open after repeated failures (`--sre-demo`) |
| Agent Compliance | `VERDICT: GO` / `NO-GO` from the compliance agent |
| Agent Marketplace | Tool **fingerprints** + trust labels at orchestrator start |
| Agent Lightning | Documented training-time boundary only |

---

## Documentation

| Doc | Topic |
|-----|--------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | First run |
| [docs/AGT_SEVEN_LAYERS.md](docs/AGT_SEVEN_LAYERS.md) | Honest 7-layer map |
| [docs/ADDING_AGENTS.md](docs/ADDING_AGENTS.md) | Spec-driven agents |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Providers, env vars |

---

## License

MIT (lab code). Upstream [Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit) is Microsoft MIT open source.
