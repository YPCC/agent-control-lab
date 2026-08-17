# Runtime, Marketplace, Compliance demos

These features are **additive**. Default `agent-control-lab` behaves as before
(fingerprints, no kill switch, no marketplace enforce).

## 1. Runtime kill switch

```bash
# All tool calls denied via RuntimeGuard (before LiteGovernor)
agent-control-lab --kill-switch

# Or:
export AGT_KILL_SWITCH=1
agent-control-lab
unset AGT_KILL_SWITCH
```

Look for `[Runtime] BLOCKED` and audit rows with `"layer": "runtime"`.

## 2. Audit-driven compliance evidence

After every successful pipeline start that reaches the end of orchestration:

```text
output/compliance_evidence.json
```

Built from denials in `output/governance_audit.jsonl` (illustrative OWASP Agentic map).

```bash
agent-control-lab
cat output/compliance_evidence.json
```

## 3. Marketplace Ed25519 (optional)

```bash
# One-time (writes gitignored private key + public key + signed catalog)
agent-control-lab --marketplace-init

# Normal run still works (verify is informational when enforce=false)
agent-control-lab

# Demo verify failure:
agent-control-lab --marketplace-tamper
agent-control-lab --marketplace-enforce   # should exit with rejected tools

# Restore:
agent-control-lab --marketplace-sign
agent-control-lab --marketplace-enforce   # should pass
```

Config (`config/config.yaml`):

```yaml
marketplace:
  enforce: false   # set true only when keys+catalog are ready
  keys_dir: config/marketplace/keys
  catalog_path: config/marketplace/catalog.json
```

Never commit `ed25519_private.pem`.
