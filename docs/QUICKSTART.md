# Quick start — Agent Control Lab

## Install

```bash
git clone https://github.com/YPCC/agent-control-lab.git
cd agent-control-lab
bash scripts/setup_uv.sh
source .venv/bin/activate
```

CLI: `agent-control-lab` or `acl`.

## Run

```bash
agent-control-lab
```

## SRE circuit

```bash
agent-control-lab --sre-reset
agent-control-lab --sre-demo   # repeat until CIRCUIT OPEN
agent-control-lab              # blocked
agent-control-lab --sre-reset
```

State: `output/sre_state.json`

## Marketplace language

Tools show **fingerprints** and trust labels (`catalogued` / `unknown`). These are not Ed25519 signatures.

## Docs

- [AGT_SEVEN_LAYERS.md](AGT_SEVEN_LAYERS.md) — honest status table
- [ADDING_AGENTS.md](ADDING_AGENTS.md) — extend the graph
