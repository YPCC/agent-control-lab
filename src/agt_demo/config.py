"""Load config.yaml and resolve multi-provider LLMs."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Tuple
import yaml

def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

def load_config(path: str | None = None) -> dict[str, Any]:
    p = Path(path or os.getenv("AGT_CONFIG_PATH") or repo_root() / "config" / "config.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return data

def resolve_llm(cfg: dict[str, Any]) -> Tuple[Any, str]:
    order = list(cfg.get("llm", {}).get("fallback_order") or ["xai", "openai", "google", "mock"])
    forced = os.getenv("AGT_LLM_PROVIDER", "").strip().lower()
    if forced:
        order = [forced] + [p for p in order if p != forced]
    preferred = (cfg.get("llm") or {}).get("provider") or order[0]
    if preferred not in order:
        order = [preferred] + order
    for provider in order:
        try:
            if provider == "xai" and (os.getenv("XAI_API_KEY") or (cfg.get("llm", {}).get("xai") or {}).get("api_key")):
                from langchain_openai import ChatOpenAI
                xai = cfg.get("llm", {}).get("xai") or {}
                return ChatOpenAI(model=xai.get("model", "grok-4"), api_key=os.getenv("XAI_API_KEY") or xai.get("api_key"), base_url=xai.get("base_url") or "https://api.x.ai/v1"), "xai"
            if provider == "openai" and os.getenv("OPENAI_API_KEY"):
                from langchain_openai import ChatOpenAI
                oai = cfg.get("llm", {}).get("openai") or {}
                kwargs = {"model": oai.get("model", "gpt-4o-mini"), "api_key": os.getenv("OPENAI_API_KEY")}
                if os.getenv("OPENAI_BASE_URL") or oai.get("base_url"):
                    kwargs["base_url"] = os.getenv("OPENAI_BASE_URL") or oai.get("base_url")
                return ChatOpenAI(**kwargs), "openai"
            if provider == "google" and (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"):
                from langchain_google_genai import ChatGoogleGenerativeAI
                g = cfg.get("llm", {}).get("google") or {}
                return ChatGoogleGenerativeAI(model=g.get("model", "gemini-2.5-flash")), "google"
        except Exception:
            continue
    class MockLLM:
        def bind_tools(self, tools):
            return self
        def invoke(self, messages):
            from langchain_core.messages import AIMessage
            return AIMessage(content="[mock] use tools explicitly")
    return MockLLM(), "mock"
