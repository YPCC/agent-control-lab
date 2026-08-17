# Architecture

## Two planes

Agent Control Lab separates **agent execution** from **agent governance**.

> LangGraph determines what agents do and in what sequence, while a surrounding control plane mediates policy, identity, privilege, reliability, compliance, tool trust, audit, and observability.

| Plane | Components |
|-------|------------|
| **Execution** | Spec-driven LangGraph: Knowledge → Critic → Compliance |
| **Governance** | Policy mediation, Mesh-style identity, RuntimeGuard, SRE monitor, Marketplace catalog, audit/telemetry, optional Langfuse |

## Diagram

![C4 context, container, and 7-layer AGT concept map](c4-and-seven-layer-map.jpg)

1. **C4 context** — developer/researcher, Agent Control Lab, LLM providers, Microsoft AGT (ACS), Langfuse  
2. **C4 container** — specification layer, orchestrator, execution agents, governance control plane, runtime artifacts  
3. **Logical 7-layer map** — status tags (Integrated / Projected / Partial / Illustrative / Reference only) over the workflow  

## Related

- [../AGT_SEVEN_LAYERS.md](../AGT_SEVEN_LAYERS.md) — claim hygiene per layer  
- [../RUNTIME_MARKETPLACE_COMPLIANCE.md](../RUNTIME_MARKETPLACE_COMPLIANCE.md) — demos for Runtime, Marketplace, Compliance  
