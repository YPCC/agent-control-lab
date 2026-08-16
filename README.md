# Agent Control Lab

**Package / GitHub name:** `agent-control-lab`

Spec-driven **LangGraph** multi-agent control plane under the **Microsoft Agent Governance Toolkit**, with optional **Langfuse** tracing and a practical showcase of all **7 AGT layers**.

> Blog: [Introducing the Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)

## Default interaction graph

```text
knowledge → critic → compliance → END
```

| Agent | Role | Spec |
|-------|------|------|
| **knowledge** | Generate RDF + HTML explorer | `config/agents/knowledge.yaml` |
| **critic** | Validate & grade quality | `config/agents/critic.yaml` |
| **compliance** | Final GO / NO-GO gate | `config/agents/compliance.yaml` |

## Quick start

```bash
git clone https://github.com/YPCC/agent-control-lab.git
cd agent-control-lab
bash scripts/setup_uv.sh
source .venv/bin/activate

# Optional: XAI_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY
# Optional Langfuse: LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY

agent-control-lab   # or: acl
```

Without API keys the demo uses a mock LLM; governance and the graph still run.

## How to see the 7 AGT layers

| # | AGT component | What to look for |
|---|---------------|------------------|
| 1 | Agent OS | `[GOVERNANCE] ALLOWED` / `BLOCKED` |
| 2 | Agent Mesh | `did:acl:…` + trust score |
| 3 | Agent Runtime | Destructive tools denied (ring 0) |
| 4 | Agent SRE | Success window / circuit helpers |
| 5 | Agent Compliance | `VERDICT: GO` / `NO-GO` |
| 6 | Agent Marketplace | Signed tool catalog at start |
| 7 | Agent Lightning | Training-time (documented only) |

Details: [docs/AGT_SEVEN_LAYERS.md](docs/AGT_SEVEN_LAYERS.md) · [docs/QUICKSTART.md](docs/QUICKSTART.md)

## Dashboards

```bash
streamlit run dashboards/companion_app.py --server.port 8502
bash scripts/launch_official_dashboard.sh
```

## License

MIT (lab code). Upstream AGT is Microsoft MIT open source.
