"""Shared HTTP clients with retry + backoff for multiple AI providers.

Supports:
- Anthropic (Claude) — Messages API + web_search tool (visibility testing only)
- DeepSeek — OpenAI-compatible Chat Completions (diagnostics, optimization, extraction)
- Perplexity (Sonar) — OpenAI-compatible Chat Completions
- OpenAI (ChatGPT) — Responses API + web_search tool
- Google Gemini — Gemini API + Google Search grounding

All services should use the provider-specific functions instead of raw httpx.
"""
import asyncio
import httpx
from app.core.config import get_settings

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]  # seconds — exponential-ish backoff


# ── Retry helper ────────────────────────────────────────────────

async def _retry_request(
    make_request,
    *,
    retryable_statuses: tuple[int, ...] = (429, 529),
    provider: str = "API",
) -> dict:
    """Generic retry wrapper. `make_request` is an async callable that
    returns an httpx.Response."""
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await make_request()

            if resp.status_code in retryable_statuses:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                retry_after = resp.headers.get("retry-after")
                if retry_after:
                    try:
                        delay = max(delay, int(retry_after))
                    except ValueError:
                        pass
                print(
                    f"[AgentShelf] {provider} {resp.status_code}, "
                    f"retry {attempt + 1}/{MAX_RETRIES} in {delay}s"
                )
                last_error = f"HTTP {resp.status_code}"
                await asyncio.sleep(delay)
                continue

            resp.raise_for_status()
            return resp.json()

        except httpx.TimeoutException:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            print(
                f"[AgentShelf] {provider} timeout, "
                f"retry {attempt + 1}/{MAX_RETRIES} in {delay}s"
            )
            last_error = "timeout"
            await asyncio.sleep(delay)
            continue

    raise RuntimeError(f"{provider} failed after {MAX_RETRIES} retries: {last_error}")


# ── Anthropic (Claude) — used ONLY for visibility testing ───────

async def anthropic_request(
    *,
    system: str,
    user_message: str,
    model: str | None = None,
    max_tokens: int = 1024,
    tools: list | None = None,
    timeout: float = 60.0,
) -> dict:
    """Make an Anthropic API request with automatic retry on 429/529."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    body: dict = {
        "model": model or settings.anthropic_model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_message}],
    }
    if tools:
        body["tools"] = tools

    async def _do():
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            )

    return await _retry_request(_do, provider="Anthropic")


# ── DeepSeek (OpenAI-compatible) ────────────────────────────────

async def deepseek_request(
    *,
    system: str,
    user_message: str,
    model: str | None = None,
    max_tokens: int = 1024,
    timeout: float = 60.0,
) -> dict:
    """Make a DeepSeek API request (OpenAI-compatible format).

    Used for: diagnostics, optimization, query generation, extraction.
    """
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise ValueError("DEEPSEEK_API_KEY not set")

    body = {
        "model": model or settings.deepseek_model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
    }

    async def _do():
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )

    return await _retry_request(_do, provider="DeepSeek")


# ── Google Gemini (with Google Search grounding) ────────────────

async def gemini_request(
    *,
    system: str,
    user_message: str,
    model: str = "gemini-2.5-flash",
    max_tokens: int = 2048,
    timeout: float = 60.0,
    use_search: bool = True,
    json_mode: bool = False,
) -> dict:
    """Make a Gemini API request, optionally with Google Search grounding.

    Used for: visibility testing (use_search=True), optimization (use_search=False).
    json_mode=True forces Gemini to return pure JSON (no markdown wrapping).
    """
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY not set")

    gen_config = {"maxOutputTokens": max_tokens}
    if json_mode:
        gen_config["responseMimeType"] = "application/json"

    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig": gen_config,
    }
    if use_search:
        body["tools"] = [{"google_search": {}}]

    async def _do():
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.gemini_api_key}",
                headers={"Content-Type": "application/json"},
                json=body,
            )

    return await _retry_request(_do, provider="Gemini")


# ── Perplexity (Sonar) ──────────────────────────────────────────

async def perplexity_request(
    *,
    system: str,
    user_message: str,
    model: str = "sonar",
    max_tokens: int = 1024,
    timeout: float = 60.0,
) -> dict:
    """Make a Perplexity Sonar API request (OpenAI-compatible format).

    Sonar has built-in web search — no need to specify tools.
    Response format: OpenAI Chat Completions style.
    """
    settings = get_settings()
    if not settings.perplexity_api_key:
        raise ValueError("PERPLEXITY_API_KEY not set")

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
    }

    async def _do():
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.perplexity_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )

    return await _retry_request(_do, provider="Perplexity")


# ── OpenAI (ChatGPT) ────────────────────────────────────────────

async def openai_request(
    *,
    system: str,
    user_message: str,
    model: str = "gpt-5.4-mini",
    timeout: float = 60.0,
    **kwargs,
) -> dict:
    """Make an OpenAI Responses API request with web_search.

    Uses gpt-5.4-mini + web_search tool via Responses API.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set")

    body = {
        "model": model,
        "tools": [{"type": "web_search"}],
        "instructions": system,
        "input": user_message,
    }

    async def _do():
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )

    return await _retry_request(_do, provider="OpenAI")


# ── Response parsing helpers ─────────────────────────────────────

def extract_text(response: dict) -> str:
    """Extract text content from Anthropic API response."""
    text = ""
    for block in response.get("content", []):
        if block.get("type") == "text":
            text += block.get("text", "")
    return text


def extract_text_deepseek(response: dict) -> str:
    """Extract text from DeepSeek (OpenAI-compatible) response."""
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return ""


def extract_text_gemini(response: dict) -> str:
    """Extract text from Gemini API response."""
    text = ""
    for candidate in response.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                text += part["text"]
    return text


def extract_citations_gemini(response: dict) -> list[str]:
    """Extract citation URLs from Gemini grounding metadata."""
    urls = []
    for candidate in response.get("candidates", []):
        metadata = candidate.get("groundingMetadata", {})
        for chunk in metadata.get("groundingChunks", []):
            web = chunk.get("web", {})
            uri = web.get("uri", "")
            if uri:
                urls.append(uri)
    return urls


def extract_text_perplexity(response: dict) -> str:
    """Extract text from Perplexity (OpenAI-compatible) response."""
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return ""


def extract_citations_perplexity(response: dict) -> list[str]:
    """Extract citation URLs from Perplexity response."""
    return response.get("citations", [])


def extract_text_openai(response: dict) -> str:
    """Extract text from OpenAI Chat Completions response."""
    # Chat Completions format
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        pass
    # Responses API fallback
    if response.get("output_text"):
        return response["output_text"]
    text = ""
    for item in response.get("output", []):
        if item.get("type") == "message":
            for block in item.get("content", []):
                if block.get("type") == "output_text":
                    text += block.get("text", "")
    return text


def extract_citations_openai(response: dict) -> list[str]:
    """Extract citation URLs from OpenAI response (Chat Completions or Responses API)."""
    urls = []
    # Chat Completions: citations in message annotations
    try:
        msg = response["choices"][0]["message"]
        for ann in msg.get("annotations", []):
            if ann.get("type") == "url_citation":
                url = ann.get("url", "")
                if url:
                    urls.append(url)
    except (KeyError, IndexError):
        pass
    # Responses API fallback
    for item in response.get("output", []):
        if item.get("type") == "message":
            for block in item.get("content", []):
                for ann in block.get("annotations", []):
                    if ann.get("type") == "url_citation":
                        url = ann.get("url", "")
                        if url:
                            urls.append(url)
    return urls
