# Marketplace keys & catalog

- `ed25519_public.pem` — committed (verify)
- `ed25519_private.pem` — **local only**, gitignored (sign)
- `catalog.json` — signed tool manifests

Generate locally:

```bash
agent-control-lab --marketplace-init
```
