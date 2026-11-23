"""FastAPI application: serves the advisor UI and the /api/advice endpoint.

Responsibilities
- Mount static files for the single-page front-end.
- Attach security headers, CORS policy, GZip compression and rate limiting.
- Expose ``POST /api/advice`` which builds and returns an :class:`AirPlan`.
"""

import logging
from collections.abc import Callable
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse

from .config import Settings
from .llm import AnthropicTextGenerator, TextGenerator
from .models import AirPlan, AirRequest
from .planner import abuild_plan

logger = logging.getLogger(__name__)

__all__ = ["app", "create_app"]

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

# Allowed CORS origins — production Vercel domain and local dev.
ALLOWED_ORIGINS = [
    "https://cleanair-zeta.vercel.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# ---------------------------------------------------------------------------
# Rate limiter (uses slowapi which is already installed)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


def _rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a JSON 429 when the client exceeds the rate limit."""
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


def create_app(
    settings: Settings | None = None,
    generator: TextGenerator | None = None,
    today_provider: Callable[[], date] = date.today,
) -> FastAPI:
    """Build and return the FastAPI application instance.

    Parameters
    ----------
    settings:
        Runtime configuration; defaults to ``Settings.from_env()``.
    generator:
        LLM text generator; built from *settings* when not supplied.
    today_provider:
        Callable returning today's date (injectable for testing).
    """
    settings = settings or Settings.from_env()
    if generator is None and settings.anthropic_api_key:
        generator = AnthropicTextGenerator(
            settings.anthropic_api_key, settings.model, settings.request_timeout
        )

    application = FastAPI(title="Clean Air Companion", version="1.0.0")

    # --- GZip compression (responses ≥ 500 bytes) ---------------------
    application.add_middleware(GZipMiddleware, minimum_size=500)

    # --- Rate limiter -------------------------------------------------
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    # --- CORS ---------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Attach hardened security headers to every response."""
        response: Response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        # Cache static assets aggressively; API responses must not be cached.
        if request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "public, max-age=86400, immutable"
        return response

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        """Serve the single-page front-end."""
        return FileResponse(STATIC_DIR / "index.html")

    @application.post("/api/advice", response_model=AirPlan)
    @limiter.limit("30/minute")
    async def create_advice(request: Request, body: AirRequest) -> AirPlan:
        """Generate a personalised clean-air plan from household context."""
        return await abuild_plan(body, today=today_provider(), generator=generator)

    return application


app = create_app()
