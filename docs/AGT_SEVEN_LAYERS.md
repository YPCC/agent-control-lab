# AGT seven-layer concept map (honest status)

Source framing: [Microsoft Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)

This lab does **not** reimplement Microsoft’s seven packages. It makes governance **visible** inside a LangGraph control loop using **integrations** and **projections**.

| AGT concept | Status | What the code does |
|-------------|--------|--------------------|
| **Agent OS / ACS** | **Integrated** | `check_policy()` — LiteGovernor allow/deny; optional ACS at `PRE_TOOL_CALL` (`EVALUATE_ONLY`); **host** raises `PermissionError` and writes audit JSONL |
| **Agent Mesh** | **Projected** | Deterministic `did:acl:…` + trust score/tier per agent node — **not** Ed25519 Mesh / IATP |
| **Agent Runtime** | **Partial** | Action→ring map; ring 0 (destructive) denied; kill-switch helper — **not** a hypervisor/sandbox |
| **Agent SRE** | **Partial** | **Persistent** `output/sre_state.json` window, error budget, circuit breaker across runs (`--sre-demo`) |
| **Agent Compliance** | **Illustrative** | Compliance agent GO/NO-GO + light OWASP Agentic evidence mapping from denials |
| **Agent Marketplace** | **Projected** | Tool **fingerprints** (SHA-256 of manifest id) + trust labels — **not** cryptographic signatures |
| **Agent Lightning** | **Reference only** | Training-time RL governance boundary; not implemented here |

## SRE circuit demo

```bash
agent-control-lab --sre-reset          # clear state
agent-control-lab --sre-demo           # run 1: forced failure
agent-control-lab --sre-demo           # … repeat until CIRCUIT OPEN
agent-control-lab                      # blocked while open
agent-control-lab --sre-reset          # recover
```

## Recommended claims

- Prefer: *“seven-layer AGT concept map with selected integrations and lab projections.”*
- Avoid: *“implements all seven AGT packages.”*
