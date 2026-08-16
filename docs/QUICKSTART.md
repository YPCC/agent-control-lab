# Quick start — Agent Control Lab

## 1. Environment

```bash
cd agent-control-lab
bash scripts/setup_uv.sh
source .venv/bin/activate
```

CLI: `agent-control-lab` or `acl`.

## 2. Credentials (optional)

| Variable | Purpose |
|----------|---------|
| `XAI_API_KEY` | Grok |
| `OPENAI_API_KEY` | OpenAI / compatible |
| `GOOGLE_API_KEY` | Gemini API |
| `GOOGLE_APPLICATION_CREDENTIALS` + `GOOGLE_CLOUD_PROJECT` | Vertex ADC |
| `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` | Tracing |
| `LANGFUSE_HOST` | Langfuse endpoint |

No keys → mock LLM; governance and the 7-layer hooks still run.

## 3. Run

```bash
agent-control-lab
```

Expect: 7-layer banner → agent registry → knowledge → critic → compliance → `VERDICT: GO`.

## 4. See the 7 AGT layers

| Layer | Signal |
|-------|--------|
| Agent OS | `[GOVERNANCE] ALLOWED` / `BLOCKED` |
| Agent Mesh | `did:acl:…` / trust score |
| Agent Runtime | Destructive tools denied |
| Agent SRE | Success / circuit helpers |
| Agent Compliance | `VERDICT: GO` |
| Agent Marketplace | Signed tool catalog |
| Agent Lightning | Documented only (training-time) |

Details: [AGT_SEVEN_LAYERS.md](AGT_SEVEN_LAYERS.md)

## 5. Dashboards

```bash
streamlit run dashboards/companion_app.py --server.port 8502
bash scripts/launch_official_dashboard.sh
```
