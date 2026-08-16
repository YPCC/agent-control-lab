# Mapping the 7 AGT components to Agent Control Lab

Source: https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/

| # | AGT component | Lab showcase |
|---|---------------|--------------|
| 1 | Agent OS | LiteGovernor + ACS/Rego on every tool call |
| 2 | Agent Mesh | did:acl + trust score per agent |
| 3 | Agent Runtime | Privilege rings; destructive tools blocked |
| 4 | Agent SRE | Success window, error budget, circuit breaker |
| 5 | Agent Compliance | Compliance agent GO/NO-GO + OWASP evidence |
| 6 | Agent Marketplace | Signed tool catalog / trust tiers |
| 7 | Agent Lightning | Training-time counterpart (documented; not in runtime graph) |

Graph: knowledge → critic → compliance → END

Langfuse optional: LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY

These are lab projections of the real AGT packages for teaching and demos.
