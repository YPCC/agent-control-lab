# Quick start — Agent Control Lab

## Install

```bash
git clone https://github.com/YPCC/agent-control-lab.git
cd agent-control-lab
bash scripts/setup_uv.sh
source .venv/bin/activate
```

CLI: `agent-control-lab` or `acl`.

## Baseline demo (unchanged)

```bash
agent-control-lab
```

## Additive demos

See [RUNTIME_MARKETPLACE_COMPLIANCE.md](RUNTIME_MARKETPLACE_COMPLIANCE.md).

```bash
# SRE circuit
agent-control-lab --sre-reset
agent-control-lab --sre-demo   # repeat until CIRCUIT OPEN

# Runtime kill switch
agent-control-lab --kill-switch

# Marketplace Ed25519
agent-control-lab --marketplace-init
agent-control-lab --marketplace-tamper
agent-control-lab --marketplace-enforce
agent-control-lab --marketplace-sign
```

## Docs

- [AGT_SEVEN_LAYERS.md](AGT_SEVEN_LAYERS.md)
- [RUNTIME_MARKETPLACE_COMPLIANCE.md](RUNTIME_MARKETPLACE_COMPLIANCE.md)
- [ADDING_AGENTS.md](ADDING_AGENTS.md)
