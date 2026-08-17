# AGT seven-layer concept map (honest status)

Source framing: [Microsoft Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)

This lab does **not** reimplement Microsoft’s seven packages. It makes governance **visible** inside a LangGraph control loop using **integrations** and **projections**.

| AGT concept | Status | What the code does |
|-------------|--------|--------------------|
| **Agent OS / ACS** | **Integrated** | `check_policy()` — RuntimeGuard → LiteGovernor → optional ACS (`EVALUATE_ONLY`); **host** raises `PermissionError` + audit JSONL |
| **Agent Mesh** | **Projected** | Deterministic `did:acl:…` + trust score/tier — **not** Ed25519 Mesh / IATP |
| **Agent Runtime** | **Partial** | Privilege rings + **kill switch** wired into `check_policy` (`--kill-switch` / `AGT_KILL_SWITCH`) — **not** a hypervisor |
| **Agent SRE** | **Partial** | Persistent `output/sre_state.json`, circuit breaker (`--sre-demo` / `--sre-reset`) |
| **Agent Compliance** | **Illustrative** | GO/NO-GO agent + **audit →** `output/compliance_evidence.json` (light OWASP map) |
| **Agent Marketplace** | **Projected** | Fingerprints always; **optional Ed25519** sign/verify (`--marketplace-init`, `--marketplace-enforce`) |
| **Agent Lightning** | **Reference only** | Training-time RL boundary; not implemented here |

## Recommended claims

- Prefer: *“seven-layer AGT concept map with selected integrations and lab projections.”*
- Avoid: *“implements all seven AGT packages.”*
