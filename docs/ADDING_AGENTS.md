# Adding agents

1. Create `config/agents/<id>.yaml` (AgentSpec)
2. Implement `src/agt_demo/agents/<id>_agent.py` with `run_*_agent`
3. Wire nodes/edges in `config/graphs/default.yaml`
4. Run `agent-control-lab`

Specs declare who the agent is and what it may do. The graph declares how agents talk. LangGraph executes. AGT/ACS enforce boundaries.
