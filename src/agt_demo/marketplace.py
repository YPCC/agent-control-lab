"""Marketplace projection: tool catalog fingerprints + optional Ed25519 sign/verify."""

from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agt_demo.agt_layers import MarketplaceTool, _fingerprint
from agt_demo.telemetry import emit_event

logger = logging.getLogger("agt_demo.marketplace")

DEFAULT_TOOLS = [
    "generate_rdf_kg",
    "validate_rdf",
    "create_rdf_infographic",
    "critique_rdf",
    "list_artifacts",
    "read_artifact",
    "compliance_verdict",
]


def _keys_dir(cfg: dict) -> Path:
    from agt_demo.config import repo_root

    rel = (cfg.get("marketplace") or {}).get("keys_dir", "config/marketplace/keys")
    return repo_root() / rel


def _catalog_path(cfg: dict) -> Path:
    from agt_demo.config import repo_root

    rel = (cfg.get("marketplace") or {}).get(
        "catalog_path", "config/marketplace/catalog.json"
    )
    return repo_root() / rel


def private_key_path(cfg: dict) -> Path:
    return _keys_dir(cfg) / "ed25519_private.pem"


def public_key_path(cfg: dict) -> Path:
    return _keys_dir(cfg) / "ed25519_public.pem"


def init_keypair(cfg: dict) -> Tuple[Path, Path]:
    """Generate Ed25519 keypair. Private key must not be committed."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization

    kd = _keys_dir(cfg)
    kd.mkdir(parents=True, exist_ok=True)
    priv_path = private_key_path(cfg)
    pub_path = public_key_path(cfg)

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    pub_path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    try:
        priv_path.chmod(0o600)
    except OSError:
        pass
    print(f"  [Marketplace] keypair → {pub_path.name} (+ private, gitignored)")
    return priv_path, pub_path


def _load_private(cfg: dict):
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    path = private_key_path(cfg)
    if not path.exists():
        raise FileNotFoundError(f"Missing private key: {path} — run marketplace-init")
    return load_pem_private_key(path.read_bytes(), password=None)


def _load_public(cfg: dict):
    from cryptography.hazmat.primitives.serialization import load_pem_public_key

    path = public_key_path(cfg)
    if not path.exists():
        return None
    return load_pem_public_key(path.read_bytes())


def _canonical_payload(name: str, version: str = "1.0") -> bytes:
    obj = {"name": name, "version": version, "schema": "acl-tool-v1"}
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_catalog(cfg: dict, tool_names: Optional[List[str]] = None) -> Path:
    """Sign tool manifests with private key; write catalog.json."""
    names = tool_names or DEFAULT_TOOLS
    private_key = _load_private(cfg)
    entries = []
    for n in names:
        payload = _canonical_payload(n)
        sig = private_key.sign(payload)
        entries.append(
            {
                "name": n,
                "version": "1.0",
                "fingerprint": _fingerprint(n),
                "signature_b64": base64.b64encode(sig).decode("ascii"),
                "trust_tier": "catalogued",
            }
        )
    catalog = {
        "schema": "acl-marketplace-catalog-v1",
        "signed_at": datetime.now(timezone.utc).isoformat(),
        "tools": entries,
    }
    path = _catalog_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    print(f"  [Marketplace] signed catalog → {path} ({len(entries)} tools)")
    return path


def verify_entry(public_key, entry: dict) -> bool:
    if public_key is None:
        return False
    try:
        sig = base64.b64decode(entry["signature_b64"])
        payload = _canonical_payload(entry["name"], entry.get("version", "1.0"))
        public_key.verify(sig, payload)
        return True
    except Exception:
        return False


def load_and_verify_catalog(tool_names: List[str], cfg: dict) -> List[MarketplaceTool]:
    """Load catalog + public key when present; verify each tool."""
    enforce = bool((cfg.get("marketplace") or {}).get("enforce", False))
    catalog_path = _catalog_path(cfg)
    public_key = _load_public(cfg)

    signed_map: Dict[str, dict] = {}
    if catalog_path.exists():
        try:
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            for e in data.get("tools") or []:
                signed_map[e["name"]] = e
        except Exception as e:
            logger.warning("catalog load failed: %s", e)

    out: List[MarketplaceTool] = []
    verified = rejected = 0
    for n in tool_names:
        fp = _fingerprint(n)
        entry = signed_map.get(n)
        if entry and public_key is not None:
            ok = verify_entry(public_key, entry)
            if ok:
                out.append(
                    MarketplaceTool(
                        name=n, trust_tier="verified", fingerprint=fp, signature_ok=True
                    )
                )
                verified += 1
            else:
                tier = "rejected" if enforce else "unknown"
                out.append(
                    MarketplaceTool(
                        name=n, trust_tier=tier, fingerprint=fp, signature_ok=False
                    )
                )
                rejected += 1
                if enforce:
                    print(f"  [Marketplace] VERIFY FAIL → {n} (enforce=true)")
        elif entry:
            out.append(
                MarketplaceTool(
                    name=n, trust_tier="catalogued", fingerprint=fp, signature_ok=None
                )
            )
        else:
            known = n in DEFAULT_TOOLS
            out.append(
                MarketplaceTool(
                    name=n,
                    trust_tier="catalogued" if known else "unknown",
                    fingerprint=fp,
                    signature_ok=None,
                )
            )

    emit_event(
        "marketplace_catalog",
        attributes={
            "tools": len(out),
            "verified": verified,
            "rejected": rejected,
            "enforce": enforce,
            "mode": "ed25519" if public_key else "fingerprint",
        },
    )
    mode = "Ed25519 verify" if public_key else "fingerprints only"
    print(
        f"  [Marketplace] {len(out)} tools — verified={verified} rejected={rejected} "
        f"enforce={enforce} ({mode})"
    )
    return out


def rejected_tools(tools: List[MarketplaceTool]) -> List[str]:
    return [t.name for t in tools if t.trust_tier == "rejected"]


def tamper_catalog_for_demo(cfg: dict, tool_name: str = "generate_rdf_kg") -> Path:
    """Flip one signature byte so verify fails — for demos only."""
    path = _catalog_path(cfg)
    if not path.exists():
        raise FileNotFoundError(f"No catalog at {path}; run marketplace-init + sign first")
    data = json.loads(path.read_text(encoding="utf-8"))
    for e in data.get("tools") or []:
        if e["name"] == tool_name:
            raw = bytearray(base64.b64decode(e["signature_b64"]))
            raw[0] ^= 0xFF
            e["signature_b64"] = base64.b64encode(bytes(raw)).decode("ascii")
            e["_tampered"] = True
            break
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  [Marketplace] TAMPERED signature for {tool_name} in {path}")
    return path
