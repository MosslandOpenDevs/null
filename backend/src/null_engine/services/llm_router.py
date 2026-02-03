import json

import httpx
import structlog
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from null_engine.config import settings

logger = structlog.get_logger()

# Role → model mapping per provider
ROLE_MODEL_MAP: dict[str, tuple[str, str]] = {
    # role: (provider, model)
    "genesis_architect": ("openai", "gpt-4o"),
    "main_debater": ("openai", "gpt-4o"),
    "reaction_agent": ("openai", "gpt-4o-mini"),
    "chaos_joker": ("anthropic", "claude-sonnet-4-20250514"),
    "searcher": ("openai", "gpt-4o-mini"),
    "librarian": ("openai", "gpt-4o-mini"),
    "translator": ("openai", "gpt-4o-mini"),
    "post_writer": ("openai", "gpt-4o-mini"),
    "wiki_writer": ("openai", "gpt-4o"),
}

# Ollama role → model mapping (local dev)
OLLAMA_ROLE_MODEL_MAP: dict[str, str] = {
    "genesis_architect": "qwen2.5:14b",
    "main_debater": "llama3.2:3b",
    "reaction_agent": "llama3.2:3b",
    "chaos_joker": "llama3.2:3b",
    "searcher": "llama3.2:3b",
    "librarian": "llama3.2:3b",
    "translator": "llama3.2:3b",
    "post_writer": "llama3.2:3b",
    "wiki_writer": "qwen2.5:14b",
}

OLLAMA_DEFAULT_MODEL = "llama3.2:3b"


class LLMRouter:
    def __init__(self):
        self._openai: AsyncOpenAI | None = None
        self._anthropic: AsyncAnthropic | None = None
        self._http: httpx.AsyncClient | None = None
        self._budget_used: float = 0.0

    @property
    def openai(self) -> AsyncOpenAI:
        if not self._openai:
            self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._openai

    @property
    def anthropic(self) -> AsyncAnthropic:
        if not self._anthropic:
            self._anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._anthropic

    @property
    def http(self) -> httpx.AsyncClient:
        if not self._http:
            self._http = httpx.AsyncClient(timeout=600.0)
        return self._http

    def _get_model(self, role: str) -> tuple[str, str]:
        return ROLE_MODEL_MAP.get(role, ("openai", "gpt-4o-mini"))

    def _get_ollama_model(self, role: str) -> str:
        return OLLAMA_ROLE_MODEL_MAP.get(role, OLLAMA_DEFAULT_MODEL)

    async def _ollama_generate(self, model: str, prompt: str, temperature: float, max_tokens: int) -> str:
        url = f"{settings.ollama_base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        resp = await self.http.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")

    async def generate_text(self, role: str, prompt: str, temperature: float = 0.8, max_tokens: int = 2048) -> str:
        # Use Ollama if configured
        if settings.llm_provider == "ollama":
            try:
                model = self._get_ollama_model(role)
                result = await self._ollama_generate(model, prompt, temperature, max_tokens)
                if result:
                    return result
                logger.warning("ollama.empty_response", model=model, role=role)
                return "(LLM error — empty response)"
            except Exception:
                logger.exception("ollama.error", role=role)
                return "(LLM error — no response generated)"

        # Cloud providers
        provider, model = self._get_model(role)

        if self._budget_used >= settings.max_budget_usd:
            logger.warning("budget.exceeded", used=self._budget_used)
            provider, model = "openai", "gpt-4o-mini"

        try:
            if provider == "openai":
                resp = await self.openai.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content or ""

            elif provider == "anthropic":
                resp = await self.anthropic.messages.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.content[0].text if resp.content else ""

            else:
                raise ValueError(f"Unknown provider: {provider}")

        except Exception:
            logger.exception("llm.error", provider=provider, model=model, role=role)
            return "(LLM error — no response generated)"

    async def generate_json(self, role: str, prompt: str, max_tokens: int = 4096) -> dict | list:
        text = await self.generate_text(role, prompt, temperature=0.3, max_tokens=max_tokens)

        # Try to extract JSON from the response
        text = text.strip()
        # Handle markdown code blocks
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the text
            for start_char, end_char in [("{", "}"), ("[", "]")]:
                start = text.find(start_char)
                end = text.rfind(end_char)
                if start != -1 and end != -1 and end > start:
                    try:
                        return json.loads(text[start : end + 1])
                    except json.JSONDecodeError:
                        continue
            logger.warning("llm.json_parse_failed", text=text[:200])
            return {}


llm_router = LLMRouter()
