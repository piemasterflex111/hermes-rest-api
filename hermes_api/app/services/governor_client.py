import httpx
import httpx_sse
import json
import logging
from typing import Optional, AsyncGenerator

from ..config import Settings

logger = logging.getLogger(__name__)


class GovernorClient:
    """
    HTTP client for the Qwen request governor (port 8003).

    What the Governor does:
    - Enforces rate limits and token budgets on vLLM requests
    - Schedules requests to avoid GPU memory exhaustion
    - Logs all requests for audit/replay
    - Rejects requests gracefully when GPU is at capacity

    Why we DON'T call vLLM directly:
    - vLLM has no rate limiting — concurrent requests can OOM the GPU
    - Governor's budget tracking lets us handle backpressure gracefully
    - Governor is the single point of failure to monitor (not vLLM)

    Architecture:
        Hermes REST API (port 8010)
            ↓
        Governor (port 8003) ← request governance layer
            ↓
        vLLM (port 8001) ← GPU inference
    """

    def __init__(self, settings: Settings, session: Optional[httpx.AsyncClient] = None):
        self.settings = settings
        self.base_url = settings.governor_base_url.rstrip("/")
        self.timeout = settings.governor_timeout
        self.max_retries = settings.governor_max_retries
        self._session = session

    @property
    def session(self) -> httpx.AsyncClient:
        """Lazy session creation. Close manually or use as context manager."""
        if self._session is None or self._session.is_closed:
            self._session = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=self.timeout,
                    write=10.0,
                    pool=5.0
                ),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._session

    async def close(self):
        if self._session and not self._session.is_closed:
            await self._session.aclose()

    async def health_check(self) -> bool:
        """
        Check if Governor is reachable.

        This is the first hop in the chain. If Governor is down, we can't
        route requests — even if vLLM is up.

        Returns True if Governor responds to /health (or any known endpoint).
        """
        try:
            # Try a lightweight probe — if Governor doesn't have /health,
            # we fall back to checking the chat endpoint responds to 400/401
            resp = await self.session.get("/health", timeout=3.0)
            return resp.status_code < 500
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError):
            return False
        except Exception:
            # Governor may not have a /health endpoint — check if base URL responds
            try:
                resp = await self.session.post("/chat/completions", 
                                                content='{"invalid": true}',
                                                timeout=3.0)
                # A 400/422 means it's alive, just rejecting bad input
                return resp.status_code < 500 or resp.status_code == 400
            except Exception:
                return False

    async def send_chat(self, messages: list[dict], stream: bool = False, 
                       model: Optional[str] = None) -> httpx.Response:
        """
        Send a chat completion request through the Governor.

        This is where the actual model inference happens. The Governor:
        1. Checks rate limit / token budget
        2. Forwards to vLLM if approved
        3. Returns the response (streaming or blocking)

        Args:
            messages: OpenAI-format message array
            stream: If True, return SSE stream response
            model: Optional model override

        Returns:
            httpx.Response (stream) or completed response

        Raises:
            httpx.HTTPStatusError: Governor rejected (429, 503) or vLLM failed (500)
            httpx.ConnectError: Governor unreachable
            httpx.TimeoutException: Inference exceeded timeout
        """
        body = {
            "model": model or "default",
            "messages": messages,
            "stream": stream,
        }

        attempt = 0
        last_exc = None

        while attempt <= self.max_retries:
            try:
                resp = await self.session.post(
                    "/chat/completions",
                    json=body,
                )

                # Governor rejections — don't retry these
                if resp.status_code == 429:
                    # Rate limited — return immediately, caller should queue
                    resp_json = resp.json() if resp.text else {}
                    raise GovernorError(
                        "Request rate-limited by Governor",
                        resp.status_code,
                        resp_json.get("detail", "Rate limit exceeded")
                    )
                if resp.status_code == 503:
                    # Governor overloaded — don't retry, GPU is genuinely busy
                    raise GovernorError(
                        "Governor unavailable (GPU at capacity)",
                        resp.status_code
                    )

                return resp

            except GovernorError:
                # Don't retry 429/503
                raise
            except httpx.HTTPStatusError as exc:
                # Server error from vLLM behind Governor — retry
                self._attempt_retry(exc, attempt)
                attempt += 1
                last_exc = exc
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                self._attempt_retry(exc, attempt)
                attempt += 1
                last_exc = exc

        raise last_exc or GovernorError("Max retries exceeded")

    async def stream_chat(self, messages: list[dict], 
                         model: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream chat completion via Server-Sent Events (SSE).

        Governor forwards the SSE stream from vLLM. Each event contains
        a partial completion chunk.

        This is how the UI gets real-time responses instead of waiting
        for the full response to complete.
        """
        resp = await self.send_chat(messages, stream=True, model=model)

        async for event in aiter_sse(resp):
            # Parse SSE data
            data = event.get("data", "")
            if data == "[DONE]":
                break
            try:
                parsed = json.loads(data)
                content = parsed.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    yield content
            except (json.JSONDecodeError, KeyError):
                # Non-standard event — skip
                logger.warning("Malformed SSE event: %s", data[:200])

    def _attempt_retry(self, exc: Exception, attempt: int):
        """Log retry attempt with exponential backoff timing."""
        wait = 2 ** attempt  # 1s, 2s, 4s
        logger.warning(
            "Governor request failed (attempt %d/%d): %s — retrying in %.1fs",
            attempt + 1, self.max_retries + 1, exc, wait
        )


class GovernorError(Exception):
    """Raised when Governor rejects a request (429, 503)."""
    status_code: int
    detail: str

    def __init__(self, message: str, status_code: int = 500, detail: str = ""):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{message} (HTTP {status_code}): {detail}" if detail else f"{message} (HTTP {status_code})")


async def aiter_sse(response: httpx.Response):
    """
    Minimal SSE event parser.

    Real SSE: 'data: {"content": "Hello"}\n\n'
    We yield dicts with 'data' key for each event block.
    """
    buffer = ""
    
    async for chunk in response.aiter_bytes():
        buffer += chunk.decode("utf-8", errors="replace")
        
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            for line in block.split("\n"):
                if line.startswith("data: "):
                    yield {"data": line[6:]}
